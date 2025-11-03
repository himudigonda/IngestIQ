import openai
import chromadb
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from core import schemas
from core.config import settings

router = APIRouter()

# --- CLIENT INITIALIZATION ---
# Initialize clients when the module is loaded.
try:
    # Initialize OpenAI client with optional custom endpoint
    openai_kwargs = {"api_key": settings.OPENAI_API_KEY}
    if settings.OPENAI_ENDPOINT:
        openai_kwargs["base_url"] = settings.OPENAI_ENDPOINT
    openai_client = openai.OpenAI(**openai_kwargs)
    
    # Initialize ChromaDB client
    chroma_client = chromadb.HttpClient(host="chroma", port=8000)
    vector_collection = chroma_client.get_collection(name="ingestiq_content")
except Exception as e:
    print(f"[ERROR] Failed to initialize clients for query endpoint: {e}")
    openai_client = None
    vector_collection = None

# --- PROMPT ENGINEERING ---
RAG_PROMPT_TEMPLATE = """
You are an expert assistant for the company. Your task is to answer the user's question based ONLY on the provided context.

Do not use any external knowledge or make up information.

If the answer is not found in the context, you MUST state that you could not find an answer in the provided documents.

For each piece of information you use, you must cite the source file path at the end of the sentence, like this: "The policy states that employees get 20 days of paid time off [source: local_data/client_abc/hr_policy.pdf]."

CONTEXT:

---
{context}
---

USER QUESTION:

{query}

ANSWER:

"""


@router.post(
    "/query",
    tags=["Query"],
    # No response model because we are streaming
)
async def query_endpoint(request: schemas.QueryRequest):
    """
    Accepts a user query, retrieves relevant context from the vector store,
    and generates an answer using an LLM.
    """
    if not openai_client or not vector_collection:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Query service is not properly configured."
        )

    async def stream_rag_response():
        # 1. RETRIEVE: Get embedding for the user's query
        try:
            query_embedding_response = openai_client.embeddings.create(
                input=[request.query],
                model=settings.OPENAI_EMBEDDINGS_MODEL
            )
            query_embedding = query_embedding_response.data[0].embedding
        except Exception as e:
            print(f"[ERROR] Failed to generate query embedding: {e}")
            yield f"Error: Could not generate embedding for the query. Details: {e}"
            return

        # 2. RETRIEVE: Query ChromaDB with a client_id filter
        try:
            results = vector_collection.query(
                query_embeddings=[query_embedding],
                n_results=5,
                where={"client_id": request.client_id}
            )
            
            context_chunks = results['documents'][0]
            metadatas = results['metadatas'][0]

            if not context_chunks:
                yield "I could not find any relevant documents for your client ID to answer this question."
                return

        except Exception as e:
            print(f"[ERROR] Failed to query ChromaDB: {e}")
            yield f"Error: Could not query the vector database. Details: {e}"
            return

        # 3. AUGMENT: Construct the prompt
        context_string = "\n\n---\n\n".join(
            f"Source: {meta['file_path']}\nContent: {doc}"
            for doc, meta in zip(context_chunks, metadatas)
        )
        
        prompt = RAG_PROMPT_TEMPLATE.format(
            context=context_string,
            query=request.query
        )

        # 4. GENERATE: Stream the response from OpenAI
        try:
            stream = openai_client.chat.completions.create(
                model=settings.OPENAI_CHAT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                stream=True,
            )
            
            # Yield each chunk of the answer as it arrives
            for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    yield content
            
            # After the answer, yield the sources for clarity
            yield "\n\n---"
            yield "\n**Sources Consulted:**\n"
            
            unique_sources = {meta['file_path'] for meta in metadatas}
            for source in sorted(list(unique_sources)):
                yield f"- {source}\n"

        except Exception as e:
            print(f"[ERROR] Failed to stream from OpenAI: {e}")
            yield f"Error: Failed to generate a response from the language model. Details: {e}"

    return StreamingResponse(stream_rag_response(), media_type="text/plain")

