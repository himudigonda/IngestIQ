from fastapi import FastAPI

app = FastAPI(
    title="IngestIQ API",
    version="0.1.0",
    description="API for the IngestIQ RAG Pipeline",
)

@app.get("/health", tags=["Monitoring"])
async def health_check():
    """Checks if the API is running."""
    return {"status": "ok"}

