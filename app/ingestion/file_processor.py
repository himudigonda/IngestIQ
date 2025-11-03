import chromadb
import openai
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings

# Initialize clients. In a real application, these might be managed more centrally.
openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
chroma_client = chromadb.HttpClient(host="chroma", port=8000)

# Ensure the collection exists. `get_or_create_collection` is idempotent.
vector_collection = chroma_client.get_or_create_collection(name="ingestiq_content")




def process_file(file_path: str, client_id: str, file_id: str, job_id: str):
    """
    The core logic for processing a single file.
    Reads, chunks, embeds, and stores a file's content.
    """

    print(f"--- Starting processing for file: {file_path} ---")

    try:
        # 1. Read Content (simple .txt reader for now)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        print(f"  > Read {len(content)} characters from file.")

        # 2. Chunk Text (Content-Aware)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        chunks = text_splitter.split_text(content)
        print(f"  > Split content into {len(chunks)} chunks.")

        if not chunks:
            print("  > No content to process. Skipping embedding and storage.")
            return

        # 3. Generate Embeddings
        response = openai_client.embeddings.create(
            input=chunks, model=settings.OPENAI_EMBEDDINGS_MODEL
        )
        embeddings = [item.embedding for item in response.data]
        print(f"  > Generated {len(embeddings)} embeddings from OpenAI.")

        # 4. Prepare for Storage
        ids = [f"{file_id}_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "client_id": client_id,
                "file_path": file_path,
                "file_id": file_id,
                "job_id": job_id,
                "chunk_number": i,
            }
            for i in range(len(chunks))
        ]

        # 5. Store in ChromaDB
        vector_collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas
        )
        print(f"  > Successfully stored {len(chunks)} vectors in ChromaDB.")
        print(f"--- Finished processing for file: {file_path} ---")

    except Exception as e:
        print(f" [!] ERROR processing file {file_path}: {e}")
        # Re-raise the exception so Airflow knows the task failed
        raise

