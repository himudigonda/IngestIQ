from contextlib import asynccontextmanager

from api import auth, ingestion, query  # <--- Added Auth
from core.database import create_db_and_tables
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application starting up...")
    create_db_and_tables()
    yield
    print("Application shutting down.")


app = FastAPI(
    title="IngestIQ Secure API",
    version="0.2.0",
    description="SOC 2 Compliant RAG Pipeline",
    lifespan=lifespan,
)


@app.get("/health", tags=["Monitoring"])
async def health_check():
    return {"status": "ok", "security_mode": "enabled"}


app.include_router(auth.router, prefix="/api/v1/auth")  # <--- Login endpoint
app.include_router(ingestion.router, prefix="/api/v1")
app.include_router(query.router, prefix="/api/v1")
