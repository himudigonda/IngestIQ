import json
import pika
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload, subqueryload

from core import models, schemas
from core.config import settings
from core.database import get_db

router = APIRouter()


def publish_to_rabbitmq(job_id: str):
    """Publishes a job ID to the ingestion queue."""
    print(f" [x] Job '{job_id}' is ready. An external trigger (like the Airflow sensor) should now pick this up.")
    # In a real system, you would have the full pika logic here. We are simulating it.



@router.post(
    "/ingest",
    response_model=schemas.IngestionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Ingestion"]
)
async def create_ingestion_job(
    request: schemas.IngestionRequest, db: Session = Depends(get_db)
):
    """
    Accepts a new ingestion job, saves it to the database,
    and queues it for processing.
    """
    # 1. Create the main job record
    new_job = models.IngestionJob(client_id=request.client_id)
    db.add(new_job)
    
    # Pre-commit to get the job ID
    db.flush()
    
    # 2. Create records for each file associated with the job
    files_to_create = []
    for file_data in request.files:
        new_file = models.IngestionFile(
            job_id=new_job.id, 
            file_path=file_data.path,
            file_metadata=file_data.metadata
        )
        files_to_create.append(new_file)
    
    db.add_all(files_to_create)
    db.commit()
    db.refresh(new_job)


    # 3. Publish the job ID to RabbitMQ to trigger the Airflow DAG
    publish_to_rabbitmq(job_id=str(new_job.id))


    return schemas.IngestionResponse(
        job_id=new_job.id,
        message="Ingestion job created and queued for processing.",
        status=new_job.status.value,
        file_count=len(files_to_create),
    )


# --- MONITORING ENDPOINTS ---

@router.get(
    "/jobs/{job_id}",
    response_model=schemas.JobStatusResponse,
    tags=["Monitoring"]
)
async def get_job_status(job_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Retrieves the detailed status of a specific ingestion job,
    including the status of all its files and any errors.
    """
    job = db.query(models.IngestionJob).options(
        subqueryload(models.IngestionJob.files),
        subqueryload(models.IngestionJob.errors).joinedload(models.ProcessingError.file)
    ).filter(models.IngestionJob.id == job_id).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found."
        )

    file_statuses = [
        schemas.FileStatus(
            file_path=file.file_path,
            status=file.status.value,
            file_hash=file.file_hash
        ) for file in job.files
    ]
    
    error_details = [
        schemas.ErrorDetail(
            file_path=error.file.file_path,
            error_message=error.error_message,
            timestamp=error.created_at
        ) for error in job.errors
    ]

    return schemas.JobStatusResponse(
        job_id=job.id,
        client_id=job.client_id,
        status=job.status.value,
        created_at=job.created_at,
        updated_at=job.updated_at,
        files=file_statuses,
        errors=error_details,
    )


@router.get(
    "/jobs/client/{client_id}",
    response_model=schemas.JobListResponse,
    tags=["Monitoring"]
)
async def get_jobs_for_client(client_id: str, db: Session = Depends(get_db)):
    """
    Retrieves a list of all ingestion jobs for a specific client.
    """
    jobs = db.query(models.IngestionJob).options(
        joinedload(models.IngestionJob.files)
    ).filter(models.IngestionJob.client_id == client_id).order_by(
        models.IngestionJob.created_at.desc()
    ).all()

    if not jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No jobs found for client ID '{client_id}'."
        )

    job_summaries = [
        schemas.JobSummary(
            job_id=job.id,
            status=job.status.value,
            created_at=job.created_at,
            updated_at=job.updated_at,
            file_count=len(job.files)
        ) for job in jobs
    ]

    return schemas.JobListResponse(
        client_id=client_id,
        jobs=job_summaries
    )

