import json
import pika
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core import models, schemas
from app.core.config import settings
from app.core.database import get_db

router = APIRouter()


def publish_to_rabbitmq(job_id: str):
    """Publishes a job ID to the ingestion queue."""
    try:
        connection = pika.BlockingConnection(pika.URLParameters(settings.RABBITMQ_URL))
        channel = connection.channel()
        
        queue_name = "ingestion_queue"
        channel.queue_declare(queue=queue_name, durable=True)
        
        message = json.dumps({"job_id": job_id})
        
        channel.basic_publish(
            exchange="",
            routing_key=queue_name,
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
            ),
        )
        connection.close()
        print(f" [x] Sent job '{job_id}' to RabbitMQ")
    except Exception as e:
        print(f" [!] RabbitMQ connection failed: {e}")
        # In a real app, you might have a fallback or retry mechanism here
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not connect to the messaging service."
        )



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
    if not request.file_paths:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="file_paths cannot be empty."
        )
        
    for path in request.file_paths:
        new_file = models.IngestionFile(job_id=new_job.id, file_path=path)
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

