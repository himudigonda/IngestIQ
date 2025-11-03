import uuid
from pydantic import BaseModel, Field
from typing import Any


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
