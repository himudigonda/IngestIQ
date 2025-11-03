import uuid
from pydantic import BaseModel, Field


class IngestionRequest(BaseModel):
    client_id: str = Field(..., description="The unique identifier for the client.", example="client_abc")
    file_paths: list[str] = Field(
        ...,
        description="A list of local file paths to be ingested.",
        example=["local_data/client_abc/hr_policy.pdf", "local_data/client_abc/manual.docx"]
    )


class IngestionResponse(BaseModel):
    job_id: uuid.UUID = Field(..., description="The unique ID for the created ingestion job.")
    message: str = Field(..., description="A confirmation message.", example="Ingestion job created successfully.")
    status: str = Field(..., description="The initial status of the job.", example="PENDING")
    file_count: int = Field(..., description="The number of files accepted for ingestion.")

