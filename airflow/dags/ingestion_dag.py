from __future__ import annotations

import pendulum
import json
import sys
import os

# Add the app directory to Python path so we can import our application code
sys.path.insert(0, '/opt/airflow/app')

from airflow.models.dag import DAG
from airflow.operators.python import PythonOperator
from airflow.decorators import task
from airflow.models.param import Param
from sqlalchemy import create_engine, update
from sqlalchemy.orm import sessionmaker, joinedload

# Import our application code
from app.core.models import IngestionJob, IngestionFile, StatusEnum, ProcessingError
from app.ingestion.file_processor import process_file

# We need to define how to get a DB session within the Airflow task context
DATABASE_URL = "postgresql+psycopg2://ingestiq:supersecretpassword@postgres:5432/ingestiq_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session():
    return SessionLocal()


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
                "metadata": file.metadata or {},
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


def set_job_status_as_processing(**context):
    """Update the job status in Postgres to PROCESSING."""
    job_id = context["params"]["job_id"]
    
    db = get_db_session()
    try:
        stmt = update(IngestionJob).where(IngestionJob.id == job_id).values(status=StatusEnum.PROCESSING)
        db.execute(stmt)
        db.commit()
        print(f"Job {job_id} status updated to PROCESSING.")
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


with DAG(
    dag_id="ingestion_pipeline",
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    catchup=False,
    schedule=None,
    tags=["ingestion", "rag"],
    params={"job_id": Param(type="string", default="")},
) as dag:
    
    # Task 0: Set job status to PROCESSING
    set_status_processing = PythonOperator(
        task_id="set_job_status_as_processing",
        python_callable=set_job_status_as_processing,
    )

    # Task 1: Fetch the list of files to process
    files_to_process_list = get_files_for_job(job_id="{{ params.job_id }}")

    # Task 2: Dynamically map a task for each file
    # This will "fan-out" and run in parallel
    processing_tasks = process_single_file_task.expand(file_info=files_to_process_list)

    # Task 3: "Fan-in" and finalize the job status after all files are processed
    final_status = finalize_job_status(job_id="{{ params.job_id }}")
    
    # Define dependencies
    set_status_processing >> files_to_process_list >> processing_tasks >> final_status
