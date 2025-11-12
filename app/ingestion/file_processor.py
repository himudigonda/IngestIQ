import hashlib
import traceback

import chromadb
import openai
from core.config import settings
from core.models import IngestionFile, ProcessingError, StatusEnum
from ingestion.parsers import get_parser
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

# --- CLIENT INITIALIZATION ---
# These clients are initialized once when the module is imported.
if settings.OPENAI_ENDPOINT:
    # Use the Azure client if an endpoint is set
    from openai import AzureOpenAI

    openai_client = AzureOpenAI(
        api_key=settings.OPENAI_API_KEY,
        api_version=settings.OPENAI_API_VERSION,
        azure_endpoint=settings.OPENAI_ENDPOINT,
    )
else:
    # Use the standard client otherwise
    openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

chroma_client = chromadb.HttpClient(host="chroma", port=8000)

# Get ChromaDB collection
vector_collection = chroma_client.get_or_create_collection(name="ingestiq_content")


# --- HELPER FUNCTIONS ---
def calculate_file_hash(file_path: str) -> str:
    """Calculates the SHA256 hash of a file's content."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read and update hash in chunks to handle large files
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


# --- CORE PROCESSING LOGIC ---
def process_file(file_info: dict, db: Session):
    """
    The core logic for processing a single file.
    Orchestrates parsing, caching, chunking, embedding, and storage.
    Now includes robust error handling.

    Args:
        file_info: A dictionary containing file details like id, path, etc.
        db: An active SQLAlchemy session.
    """
    file_id = file_info["id"]
    file_path = file_info["path"]
    job_id = file_info["job_id"]
    client_id = file_info["client_id"]
    custom_metadata = file_info.get("metadata", {}) or {}

    print(f"--- Starting processing for file: {file_path} (ID: {file_id}) ---")

    try:
        # 1. Update file status to PROCESSING
        db.query(IngestionFile).filter(IngestionFile.id == file_id).update(
            {"status": StatusEnum.PROCESSING}
        )
        db.commit()

        # 2. Idempotency Check (CORRECTED LOGIC)
        file_hash = calculate_file_hash(file_path)
        try:
            # Atomically update the file record with the hash.
            db.query(IngestionFile).filter(IngestionFile.id == file_id).update(
                {"file_hash": file_hash}
            )
            db.commit()
        except IntegrityError:
            # This error means the (job_id, file_hash) constraint was violated.
            db.rollback()  # Rollback the failed transaction
            print(
                f"  [!] Idempotency check: File with hash {file_hash[:10]}... already processed for this job. Skipping."
            )
            # Mark this specific file instance as FAILED because it's a duplicate
            db.query(IngestionFile).filter(IngestionFile.id == file_id).update(
                {"status": StatusEnum.FAILED}
            )
            db.commit()
            return  # Stop processing this file

        # 3. Parse, Cache, Chunk, Embed, Store...
        parser = get_parser(file_path)
        content = parser.parse(file_path)

        if not content.strip():
            print("  > No content extracted. Marking as complete.")
            db.query(IngestionFile).filter(IngestionFile.id == file_id).update(
                {"status": StatusEnum.COMPLETED}
            )
            db.commit()
            return

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200, length_function=len
        )
        chunks = text_splitter.split_text(content)

        if not chunks:
            db.query(IngestionFile).filter(IngestionFile.id == file_id).update(
                {"status": StatusEnum.COMPLETED}
            )
            db.commit()
            return

        response = openai_client.embeddings.create(
            input=chunks, model=settings.OPENAI_EMBEDDINGS_MODEL
        )
        embeddings = [item.embedding for item in response.data]

        ids = [f"{file_id}_{i}" for i in range(len(chunks))]

        # --- ENHANCED METADATA ---
        metadatas = []
        for i in range(len(chunks)):
            # Start with the custom metadata provided by the user
            chunk_metadata = custom_metadata.copy()
            # Add our internal, system-level metadata
            chunk_metadata.update(
                {
                    "client_id": client_id,
                    "file_path": file_path,
                    "file_id": file_id,
                    "job_id": job_id,
                    "chunk_number": i,
                }
            )
            metadatas.append(chunk_metadata)

        vector_collection.add(
            ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas
        )

        # 4. Update file status to COMPLETED
        db.query(IngestionFile).filter(IngestionFile.id == file_id).update(
            {"status": StatusEnum.COMPLETED}
        )
        db.commit()

        print(f"--- Finished processing for file: {file_path} ---")

    except Exception as e:
        db.rollback()
        print(f" [!] ERROR processing file {file_path}: {e}")

        # Log the error to the database
        error_message = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
        error_record = ProcessingError(
            job_id=job_id, file_id=file_id, error_message=error_message
        )
        db.add(error_record)

        # Mark the specific file as FAILED
        db.query(IngestionFile).filter(IngestionFile.id == file_id).update(
            {"status": StatusEnum.FAILED}
        )
        db.commit()
