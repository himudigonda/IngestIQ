from __future__ import annotations

import pendulum
import json
import sys
import os

# Add the app directory to Python path so we can import our application code
sys.path.insert(0, '/opt/airflow/app')

from airflow.models.dag import DAG
from airflow.providers.rabbitmq.sensors.rabbitmq import RabbitMQSensor
from airflow.operators.python import PythonOperator

from sqlalchemy import create_engine, update
from sqlalchemy.orm import sessionmaker

# Import our application code
from app.core.models import IngestionJob, IngestionFile, StatusEnum
from app.ingestion.file_processor import process_file

# We need to define how to get a DB session within the Airflow task context
DATABASE_URL = "postgresql+psycopg2://ingestiq:supersecretpassword@postgres:5432/ingestiq_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session():
    return SessionLocal()


def set_job_status_as_processing(**context):
    """Update the job status in Postgres to PROCESSING."""
    message = json.loads(context["ti"].xcom_pull(task_ids="read_job_from_queue")[0])
    job_id = message['job_id']
    
    db = get_db_session()
    try:
        stmt = update(IngestionJob).where(IngestionJob.id == job_id).values(status=StatusEnum.PROCESSING)
        db.execute(stmt)
        db.commit()
        print(f"Job {job_id} status updated to PROCESSING.")
        return job_id # Pass job_id to the next task
    finally:
        db.close()


def process_all_files_for_job(**context):
    """Fetch all files for a job and process them."""
    job_id = context["ti"].xcom_pull(task_ids="set_job_status_as_processing")
    db = get_db_session()
    try:
        job = db.query(IngestionJob).filter(IngestionJob.id == job_id).first()
        if not job or not job.files:
            print(f"No files found for job {job_id}. Nothing to process.")
            return

        print(f"Found {len(job.files)} files for job {job_id}. Starting processing...")
        for file in job.files:
            # Adjust file path to be accessible from Airflow worker container
            # Files are mounted at /opt/airflow/local_data
            file_path = file.file_path
            if not os.path.isabs(file_path):
                # If relative, assume it's relative to local_data
                file_path = os.path.join("/opt/airflow", file_path)
            
            # Here we call the main processing logic for each file
            process_file(
                file_path=file_path,
                client_id=job.client_id,
                file_id=str(file.id),
                job_id=str(job.id)
            )
    finally:
        db.close()


def set_job_status_as_completed(**context):
    """Final task to mark the job as COMPLETED."""
    job_id = context["ti"].xcom_pull(task_ids="set_job_status_as_processing")
    db = get_db_session()
    try:
        stmt = update(IngestionJob).where(IngestionJob.id == job_id).values(status=StatusEnum.COMPLETED)
        db.execute(stmt)
        db.commit()
        print(f"Job {job_id} status updated to COMPLETED.")
    finally:
        db.close()



with DAG(
    dag_id="ingestion_pipeline",
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    catchup=False,
    schedule=None, # Triggered externally
    tags=["ingestion", "rag"],
) as dag:
    # Task 1: Wait for a message on the RabbitMQ queue
    read_job_from_queue = RabbitMQSensor(
        task_id="read_job_from_queue",
        rabbitmq_conn_id="amqp_default", # Airflow's default connection ID for RabbitMQ
        queue="ingestion_queue",
    )

    # Task 2: Update the job's status in our database
    set_status_processing = PythonOperator(
        task_id="set_job_status_as_processing",
        python_callable=set_job_status_as_processing,
    )

    # Task 3: The main workhorse - process all files for the job
    process_files_task = PythonOperator(
        task_id="process_all_files_for_job",
        python_callable=process_all_files_for_job,
    )

    # Task 4: Mark the job as complete
    set_status_completed = PythonOperator(
        task_id="set_job_status_as_completed",
        python_callable=set_job_status_as_completed,
    )
    
    # Define the task dependencies
    read_job_from_queue >> set_status_processing >> process_files_task >> set_status_completed
