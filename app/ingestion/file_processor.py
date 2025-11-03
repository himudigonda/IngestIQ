import chromadb
import openai
import hashlib
from pymongo import MongoClient
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings
from app.core.models import IngestionFile, StatusEnum
from app.ingestion.parsers import get_parser

# --- CLIENT INITIALIZATION ---
# These clients are initialized once when the module is imported.
openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
chroma_client = chromadb.HttpClient(host="chroma", port=8000)
mongo_client = MongoClient(settings.MONGO_URL)

# Get ChromaDB collection
vector_collection = chroma_client.get_or_create_collection(name="ingestiq_content")

# Get MongoDB database and collection
mongo_db = mongo_client["ingestiq_cache"]
raw_content_collection = mongo_db["raw_content"]




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
def process_file(file_path: str, client_id: str, file_id: str, job_id: str, db: Session):
    """
    The core logic for processing a single file.
    Orchestrates parsing, caching, chunking, embedding, and storage.
    """
    print(f"--- Starting processing for file: {file_path} ---")

    try:
        # 1. Calculate Hash and Attempt to Save (Idempotency Check)
        file_hash = calculate_file_hash(file_path)
        try:
            # Atomically update the file record with the hash.
            db.query(IngestionFile).filter(IngestionFile.id == file_id).update({"file_hash": file_hash})
            db.commit()
        except IntegrityError:
            # This error means the (job_id, file_hash) combination already exists.
            db.rollback() # Rollback the failed transaction
            print(f"  [!] Idempotency check: File with hash {file_hash[:10]}... already processed for this job. Skipping.")
            return # Stop processing this file

        # 2. Parse Content using the factory
        parser = get_parser(file_path)
        content = parser.parse(file_path)
        print(f"  > Parsed {len(content)} characters from file.")
        
        if not content.strip():
            print("  > No content extracted. Skipping further processing.")
            return

        # 3. Cache Raw Content in MongoDB
        mongo_db_document = {
            "file_id": file_id,
            "job_id": job_id,
            "client_id": client_id,
            "file_path": file_path,
            "content": content,
            "hash": file_hash,
        }
        raw_content_collection.replace_one({"file_id": file_id}, mongo_db_document, upsert=True)
        print(f"  > Cached raw text content in MongoDB.")

        # 4. Chunk Text
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        chunks = text_splitter.split_text(content)
        print(f"  > Split content into {len(chunks)} chunks.")

        if not chunks:
            return

        # 5. Generate Embeddings
        response = openai_client.embeddings.create(
            input=chunks, model=settings.OPENAI_EMBEDDINGS_MODEL
        )
        embeddings = [item.embedding for item in response.data]
        print(f"  > Generated {len(embeddings)} embeddings from OpenAI.")

        # 6. Prepare for Vector Storage
        ids = [f"{file_id}_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "client_id": client_id,
                "file_path": file_path,
                "file_id": file_id,
                "job_id": job_id,
                "chunk_number": i,
                # Add more enhanced metadata here in the future
            }
            for i in range(len(chunks))
        ]

        # 7. Store in ChromaDB
        vector_collection.add(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)
        print(f"  > Successfully stored {len(chunks)} vectors in ChromaDB.")
        print(f"--- Finished processing for file: {file_path} ---")

    except Exception as e:
        print(f" [!] ERROR processing file {file_path}: {e}")
        # In Phase 4, we will log this error to the database instead of just raising it.
        raise
