from __future__ import annotations

import pendulum
import json
import os
import pika
from sqlalchemy import create_engine, update
from sqlalchemy.orm import sessionmaker, joinedload

from airflow.models.dag import DAG
from airflow.decorators import task
from airflow.sensors.python import PythonSensor

# Import our application code
from core.models import IngestionJob, StatusEnum, ProcessingError
from ingestion.file_processor import process_file


# --- DATABASE & MESSAGE QUEUE SETUP ---
DATABASE_URL = "postgresql+psycopg2://ingestiq:supersecretpassword@postgres:5432/ingestiq_db"
RABBITMQ_URL = "amqp://ingestiq:supersecretpassword@rabbitmq:5672/"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session():
    return SessionLocal()


# --- AIRFLOW TASK CALLABLES ---
def check_for_job_message(**context):
    """
    Called by the PythonSensor. It checks RabbitMQ for a message.
    If a message is found, it pushes the job_id to XComs and returns True.
    """
    try:
        connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
        channel = connection.channel()
        method_frame, header_frame, body = channel.basic_get(queue="ingestion_queue")
        if method_frame:
            channel.basic_ack(method_frame.delivery_tag)
            connection.close()
            job_id = json.loads(body.decode('utf-8'))['job_id']
            context['ti'].xcom_push(key='job_id', value=job_id)
            print(f" [x] Received job_id '{job_id}' from RabbitMQ.")
            return True
    except pika.exceptions.AMQPConnectionError:
        print(" [!] Could not connect to RabbitMQ. Will retry.")
    except Exception as e:
        print(f" [!] An error occurred in the sensor: {e}")
    return False


@task
def set_job_to_processing(ti=None):
    job_id = ti.xcom_pull(task_ids='check_for_new_job', key='job_id')
    db = get_db_session()
    try:
        stmt = update(IngestionJob).where(IngestionJob.id == job_id).values(status=StatusEnum.PROCESSING)
        db.execute(stmt)
        db.commit()
        print(f"Job {job_id} status updated to PROCESSING.")
        return job_id
    finally:
        db.close()


@task
def get_files_for_job(job_id: str):
    """Fetches the list of files for a given job_id from Postgres."""
    db = get_db_session()
    try:
        job = db.query(IngestionJob).options(joinedload(IngestionJob.files)).filter(IngestionJob.id == job_id).first()
        if not job or not job.files:
            return []
        
        # Return a list of dictionaries, which is JSON-serializable for XComs
        files_to_process = [
            {
                "id": str(file.id),
                "path": os.path.join("/opt/airflow", file.file_path) if not os.path.isabs(file.file_path) else file.file_path,
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
    """
    A dynamically mapped task to process one file.
    It now includes its own DB session management.
    """
    db = get_db_session()
    try:
        # The main processing logic is now called here
        process_file(file_info, db)
    finally:
        db.close()


@task
def finalize_job_status(job_id: str):
    """
    Checks for errors and sets the final job status to COMPLETED or
    COMPLETED_WITH_ERRORS.
    """
    db = get_db_session()
    try:
        error_count = db.query(ProcessingError).filter(ProcessingError.job_id == job_id).count()
        
        final_status = StatusEnum.COMPLETED_WITH_ERRORS if error_count > 0 else StatusEnum.COMPLETED
        
        stmt = update(IngestionJob).where(IngestionJob.id == job_id).values(status=final_status)
        db.execute(stmt)
        db.commit()
        
        print(f"Job {job_id} finalized with status: {final_status.value}. Found {error_count} errors.")
    finally:
        db.close()


# --- DAG DEFINITION ---
with DAG(
    dag_id="ingestion_pipeline",
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    catchup=False,
    schedule=None,
    tags=["ingestion", "rag"],
) as dag:
    
    # Task 1: Wait for a message and get the job_id
    check_for_new_job = PythonSensor(
        task_id="check_for_new_job",
        python_callable=check_for_job_message,
        poke_interval=5,
        timeout=300,
        mode="poke",
    )
    
    # Task 2: Set the job's status to PROCESSING
    job_id = set_job_to_processing()

    # Task 3: Get the list of files for that job
    files_list = get_files_for_job(job_id)

    # Task 4 (Fan-Out): Process each file in parallel
    processing = process_single_file_task.expand(file_info=files_list)

    # Task 5 (Fan-In): Finalize the job status after all files are done
    finalize = finalize_job_status(job_id)

    # Define the dependency chain
    check_for_new_job >> job_id
    job_id >> files_list >> processing >> finalize
