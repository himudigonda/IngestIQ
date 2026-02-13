import json
import uuid

import pika
from api.deps import CurrentUser
from core import models, schemas
from core.config import settings
from core.database import get_db
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session, joinedload, subqueryload

router = APIRouter()


def publish_to_rabbitmq(job_id: str):
    try:
        connection = pika.BlockingConnection(pika.URLParameters(settings.RABBITMQ_URL))
        channel = connection.channel()
        channel.queue_declare(queue="ingestion_queue", durable=True)
        message = json.dumps({"job_id": job_id})
        channel.basic_publish(
            exchange="",
            routing_key="ingestion_queue",
            body=message,
            properties=pika.BasicProperties(delivery_mode=2),
        )
        connection.close()
    except Exception as e:
        print(f" [!] Failed to publish to RabbitMQ: {e}")


@router.post(
    "/ingest",
    response_model=schemas.IngestionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Ingestion"],
)
async def create_ingestion_job(
    request: schemas.IngestionRequest,
    current_user: CurrentUser,
    req: Request,
    db: Session = Depends(get_db),
):
    # SOC 2 Control: Tenant Isolation
    if (
        current_user.role != models.UserRole.ADMIN
        and request.client_id != current_user.client_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. You are not authorized to ingest data for client '{request.client_id}'.",
        )

    # 1. Create Job
    new_job = models.IngestionJob(
        client_id=request.client_id, created_by=current_user.id
    )
    db.add(new_job)
    db.flush()

    files_to_create = []
    for file_data in request.files:
        new_file = models.IngestionFile(
            job_id=new_job.id,
            file_path=file_data.path,
            file_metadata=file_data.metadata,
        )
        files_to_create.append(new_file)

    db.add_all(files_to_create)

    # SOC 2 Control: Audit Logging
    audit_log = models.AuditLog(
        user_id=current_user.id,
        action="INGEST_JOB_CREATED",
        resource_type="JOB",
        resource_id=str(new_job.id),
        details={"file_count": len(files_to_create), "client_id": request.client_id},
        ip_address=req.client.host,
    )
    db.add(audit_log)

    db.commit()
    db.refresh(new_job)

    publish_to_rabbitmq(job_id=str(new_job.id))

    return schemas.IngestionResponse(
        job_id=new_job.id,
        message="Ingestion job created and queued.",
        status=new_job.status.value,
        file_count=len(files_to_create),
    )


@router.get(
    "/jobs/{job_id}", response_model=schemas.JobStatusResponse, tags=["Monitoring"]
)
async def get_job_status(
    job_id: uuid.UUID, current_user: CurrentUser, db: Session = Depends(get_db)
):
    job = (
        db.query(models.IngestionJob)
        .options(
            subqueryload(models.IngestionJob.files),
            subqueryload(models.IngestionJob.errors).joinedload(
                models.ProcessingError.file
            ),
        )
        .filter(models.IngestionJob.id == job_id)
        .first()
    )

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found.",
        )

    # SOC 2 Control: Tenant Isolation
    if (
        current_user.role != models.UserRole.ADMIN
        and job.client_id != current_user.client_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied."
        )

    file_statuses = [
        schemas.FileStatus(
            file_path=file.file_path, status=file.status.value, file_hash=file.file_hash
        )
        for file in job.files
    ]

    error_details = [
        schemas.ErrorDetail(
            file_path=error.file.file_path,
            error_message=error.error_message,
            timestamp=error.created_at,
        )
        for error in job.errors
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
    tags=["Monitoring"],
)
async def get_jobs_for_client(
    client_id: str, current_user: CurrentUser, db: Session = Depends(get_db)
):
    # SOC 2 Control: Tenant Isolation
    if (
        current_user.role != models.UserRole.ADMIN
        and client_id != current_user.client_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied."
        )

    jobs = (
        db.query(models.IngestionJob)
        .options(joinedload(models.IngestionJob.files))
        .filter(models.IngestionJob.client_id == client_id)
        .order_by(models.IngestionJob.created_at.desc())
        .all()
    )

    job_summaries = [
        schemas.JobSummary(
            job_id=job.id,
            status=job.status.value,
            created_at=job.created_at,
            updated_at=job.updated_at,
            file_count=len(job.files),
        )
        for job in jobs
    ]

    return schemas.JobListResponse(client_id=client_id, jobs=job_summaries)
