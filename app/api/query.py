import chromadb
import openai
from api.deps import CurrentUser
from core import models, schemas
from core.config import settings
from core.database import get_db
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

router = APIRouter()

# --- CLIENT INITIALIZATION ---
try:
    if settings.OPENAI_ENDPOINT:
        from openai import AzureOpenAI

        openai_client = AzureOpenAI(
            api_key=settings.OPENAI_API_KEY,
            api_version=settings.OPENAI_API_VERSION,
            azure_endpoint=settings.OPENAI_ENDPOINT,
        )
    else:
        openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

    chroma_client = chromadb.HttpClient(host="chroma", port=8000)
    vector_collection = chroma_client.get_or_create_collection(name="ingestiq_content")
except Exception as e:
    print(f"[ERROR] Failed to initialize clients: {e}")
    openai_client = None
    vector_collection = None

RAG_PROMPT_TEMPLATE = """
You are an expert assistant for the company. Your task is to answer the user's question based ONLY on the provided context.
If the answer is not found in the context, you MUST state that you could not find an answer in the provided documents.
Citations: [source: local_data/client_abc/doc.pdf]

CONTEXT:
---
{context}
---

USER QUESTION:
{query}

ANSWER:
"""


@router.post("/query", tags=["Query"])
async def query_endpoint(
    request: schemas.QueryRequest,
    current_user: CurrentUser,
    req: Request,
    db: Session = Depends(get_db),
):
    # SOC 2 Control: Tenant Isolation
    target_client_id = request.client_id
    if current_user.role != models.UserRole.ADMIN:
        if target_client_id != current_user.client_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You cannot query data for this client.",
            )
        target_client_id = current_user.client_id

    # SOC 2 Control: Audit Logging
    audit_log = models.AuditLog(
        user_id=current_user.id,
        action="QUERY_EXECUTED",
        resource_type="VECTOR_STORE",
        details={
            "query_snippet": request.query[:50] + "...",
            "client_id": target_client_id,
        },
        ip_address=req.client.host,
    )
    db.add(audit_log)
    db.commit()

    if not openai_client or not vector_collection:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Query service is not properly configured.",
        )

    async def stream_rag_response():
        try:
            query_embedding_response = openai_client.embeddings.create(
                input=[request.query], model=settings.OPENAI_EMBEDDINGS_MODEL
            )
            query_embedding = query_embedding_response.data[0].embedding
        except Exception as e:
            yield f"Error: Could not generate embedding. Details: {e}"
            return

        try:
            results = vector_collection.query(
                query_embeddings=[query_embedding],
                n_results=5,
                where={"client_id": target_client_id},
            )
            context_chunks = results["documents"][0]
            metadatas = results["metadatas"][0]

            if not context_chunks:
                yield "I could not find any relevant documents for your client ID."
                return
        except Exception as e:
            yield f"Error: Could not query vector DB. Details: {e}"
            return

        context_string = "\n\n---\n\n".join(
            f"Source: {meta['file_path']}\nContent: {doc}"
            for doc, meta in zip(context_chunks, metadatas)
        )
        prompt = RAG_PROMPT_TEMPLATE.format(context=context_string, query=request.query)

        try:
            stream = openai_client.chat.completions.create(
                model=settings.OPENAI_CHAT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                stream=True,
            )
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content

            yield "\n\n---\n**Sources Consulted:**\n"
            unique_sources = {meta["file_path"] for meta in metadatas}
            for source in sorted(list(unique_sources)):
                yield f"- {source}\n"
        except Exception as e:
            yield f"Error: Failed to generate response. Details: {e}"

    return StreamingResponse(stream_rag_response(), media_type="text/plain")
