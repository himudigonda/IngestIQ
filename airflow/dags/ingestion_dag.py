from __future__ import annotations

import json
import os

import pendulum
import pika
from airflow.decorators import task
from airflow.models.dag import DAG
from airflow.sensors.python import PythonSensor
from sqlalchemy import create_engine, update
from sqlalchemy.orm import sessionmaker

# SOC 2 Control: Secrets Management
DATABASE_URL = os.getenv("AIRFLOW__DATABASE__SQL_ALCHEMY_CONN")
RABBITMQ_URL = os.getenv("AIRFLOW__CELERY__BROKER_URL")

if not DATABASE_URL or not RABBITMQ_URL:
    raise ValueError(
        "Critical security error: Missing environment variables for DB or Queue."
    )

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session():
    return SessionLocal()


# --- AIRFLOW TASK CALLABLES ---
@task
def get_job_id_from_queue() -> str:
    """
    Checks RabbitMQ for a message. If found, it returns the job_id.
    This replaces the PythonSensor for a cleaner TaskFlow implementation.
    """
    try:
        connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
        channel = connection.channel()
        channel.queue_declare(queue="ingestion_queue", durable=True)
        method_frame, header_frame, body = channel.basic_get(queue="ingestion_queue")
        if method_frame:
            channel.basic_ack(method_frame.delivery_tag)
            connection.close()
            job_id = json.loads(body.decode("utf-8"))["job_id"]
            print(f" [x] Received job_id '{job_id}' from RabbitMQ.")
            return job_id
    except pika.exceptions.AMQPConnectionError:
        print(" [!] Could not connect to RabbitMQ.")
    except Exception as e:
        print(f" [!] An error occurred: {e}")
    # If no message, we must raise an exception to make the task retry.
    from airflow.exceptions import AirflowSkipException

    raise AirflowSkipException("No message in queue. Task will retry.")


@task
def set_job_to_processing(job_id: str):
    # Import inside the task
    from core.models import IngestionJob, StatusEnum

    db = get_db_session()
    try:
        stmt = (
            update(IngestionJob)
            .where(IngestionJob.id == job_id)
            .values(status=StatusEnum.PROCESSING)
        )
        db.execute(stmt)
        db.commit()
        print(f"Job {job_id} status updated to PROCESSING.")
        return job_id
    finally:
        db.close()


@task
def get_files_for_job(job_id: str):
    # Import inside the task
    from core.models import IngestionJob
    from sqlalchemy.orm import joinedload

    db = get_db_session()
    try:
        job = (
            db.query(IngestionJob)
            .options(joinedload(IngestionJob.files))
            .filter(IngestionJob.id == job_id)
            .first()
        )
        if not job or not job.files:
            return []

        files_to_process = [
            {
                "id": str(file.id),
                "path": os.path.join("/opt/airflow", file.file_path),
                "job_id": str(job.id),
                "client_id": job.client_id,
                "metadata": file.file_metadata or {},
            }
            for file in job.files
        ]
        print(f"Found {len(files_to_process)} files to process for job {job_id}.")
        return files_to_process
    finally:
        db.close()


@task
def process_single_file_task(file_info: dict):
    # Import inside the task
    from ingestion.file_processor import process_file

    db = get_db_session()
    try:
        process_file(file_info, db)
    finally:
        db.close()


@task
def finalize_job_status(job_id: str, processed_files: list):
    # This task now accepts a second argument to ensure it runs *after* processing.
    # Import inside the task
    from core.models import IngestionJob, ProcessingError, StatusEnum

    db = get_db_session()
    try:
        error_count = (
            db.query(ProcessingError).filter(ProcessingError.job_id == job_id).count()
        )
        final_status = (
            StatusEnum.COMPLETED_WITH_ERRORS
            if error_count > 0
            else StatusEnum.COMPLETED
        )
        stmt = (
            update(IngestionJob)
            .where(IngestionJob.id == job_id)
            .values(status=final_status)
        )
        db.execute(stmt)
        db.commit()
        print(
            f"Job {job_id} finalized with status: {final_status.value}. Found {error_count} errors."
        )
    finally:
        db.close()


# --- DAG DEFINITION ---
with DAG(
    dag_id="ingestion_pipeline",
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    catchup=False,
    schedule=None,
    tags=["ingestion", "rag"],
    default_args={"retries": 3, "retry_delay": pendulum.duration(minutes=1)},
) as dag:
    job_id = get_job_id_from_queue()
    processing_job_id = set_job_to_processing(job_id)
    files_list = get_files_for_job(processing_job_id)
    # The .expand() call creates the parallel tasks
    processed_files = process_single_file_task.expand(file_info=files_list)
    # The finalize task now depends on the output of the mapped task
    finalize_job_status(processing_job_id, processed_files)
