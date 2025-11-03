import uuid
import enum
from datetime import datetime
from sqlalchemy import create_engine, Column, String, DateTime, ForeignKey, Enum, UniqueConstraint, Text
from sqlalchemy.orm import relationship, sessionmaker, declarative_base
from sqlalchemy.dialects.postgresql import UUID, JSONB

Base = declarative_base()


class StatusEnum(enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    COMPLETED_WITH_ERRORS = "COMPLETED_WITH_ERRORS"


class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(String, nullable=False, index=True)
    status = Column(Enum(StatusEnum), nullable=False, default=StatusEnum.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    files = relationship("IngestionFile", back_populates="job")
    errors = relationship("ProcessingError", back_populates="job")


class IngestionFile(Base):
    __tablename__ = "ingestion_files"
    __table_args__ = (
        UniqueConstraint('job_id', 'file_hash', name='_job_hash_uc'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("ingestion_jobs.id"), nullable=False)
    file_path = Column(String, nullable=False)
    status = Column(Enum(StatusEnum), nullable=False, default=StatusEnum.PENDING)
    file_hash = Column(String, nullable=True, index=True)
    metadata = Column(JSONB, nullable=True)

    job = relationship("IngestionJob", back_populates="files")
    error = relationship("ProcessingError", back_populates="file", uselist=False)


class ProcessingError(Base):
    __tablename__ = "processing_errors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("ingestion_jobs.id"), nullable=False)
    file_id = Column(UUID(as_uuid=True), ForeignKey("ingestion_files.id"), nullable=False)
    error_message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    job = relationship("IngestionJob", back_populates="errors")
    file = relationship("IngestionFile", back_populates="error")

