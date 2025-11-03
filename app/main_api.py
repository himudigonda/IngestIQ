from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api import ingestion # Import the new router
from app.core.database import create_db_and_tables # Import the init function


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application starting up...")
    create_db_and_tables() # Create tables on startup
    yield
    print("Application shutting down.")


app = FastAPI(
    title="IngestIQ API",
    version="0.1.0",
    description="API for the IngestIQ RAG Pipeline",
    lifespan=lifespan
)


@app.get("/health", tags=["Monitoring"])
async def health_check():
    """Checks if the API is running."""
    return {"status": "ok"}


# Include the ingestion router in our main app
app.include_router(ingestion.router, prefix="/api/v1")
