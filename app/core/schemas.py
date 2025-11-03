import uuid
from pydantic import BaseModel, Field
from typing import Any, List
from datetime import datetime


class FileIngestionData(BaseModel):
    path: str = Field(..., description="The local file path to be ingested.", example="local_data/client_abc/hr_policy.pdf")
    metadata: dict[str, Any] | None = Field(None, description="Optional dictionary of custom metadata.", example={"document_type": "HR", "year": 2024})


class IngestionRequest(BaseModel):
    client_id: str = Field(..., description="The unique identifier for the client.", example="client_abc")
    files: list[FileIngestionData] = Field(
        ...,
        description="A list of file objects to be ingested.",
        min_length=1
    )


class IngestionResponse(BaseModel):
    job_id: uuid.UUID = Field(..., description="The unique ID for the created ingestion job.")
    message: str = Field(..., description="A confirmation message.", example="Ingestion job created successfully.")
    status: str = Field(..., description="The initial status of the job.", example="PENDING")
    file_count: int = Field(..., description="The number of files accepted for ingestion.")


# --- QUERY SCHEMAS (New) ---
class QueryRequest(BaseModel):
    client_id: str = Field(..., description="The client whose data should be queried.", example="client_abc")
    query: str = Field(..., description="The user's question.", example="What is the policy on sick leave?")


# We will not use a response model for the endpoint itself, as it will be a streaming response.
# However, we can define a model for the source documents that will be cited.
class SourceDocument(BaseModel):
    file_path: str
    metadata: dict[str, Any]
    content: str


# --- ANALYTICS & STATUS SCHEMAS ---
class ErrorDetail(BaseModel):
    """Schema for a single processing error."""
    file_path: str
    error_message: str
    timestamp: datetime


class FileStatus(BaseModel):
    """Schema for the status of a single file within a job."""
    file_path: str
    status: str
    file_hash: str | None = None


class JobStatusResponse(BaseModel):
    """Detailed status response for a single ingestion job."""
    job_id: uuid.UUID
    client_id: str
    status: str
    created_at: datetime
    updated_at: datetime
    files: List[FileStatus]
    errors: List[ErrorDetail]


class JobSummary(BaseModel):
    """High-level summary of an ingestion job for a list view."""
    job_id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime
    file_count: int


class JobListResponse(BaseModel):
    """Response model for a list of job summaries."""
    client_id: str
    jobs: List[JobSummary]
