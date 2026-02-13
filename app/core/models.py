import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class StatusEnum(enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    COMPLETED_WITH_ERRORS = "COMPLETED_WITH_ERRORS"


class UserRole(enum.Enum):
    ADMIN = "admin"
    USER = "user"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(Enum(UserRole), default=UserRole.USER)
    # Tenant Isolation: A user belongs to one client context
    client_id = Column(String, nullable=False, index=True)


class AuditLog(Base):
    """Immutable record of system actions for SOC 2 compliance."""

    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False)  # e.g., "INGEST", "QUERY"
    resource_type = Column(String, nullable=False)  # e.g., "JOB", "DOCUMENT"
    resource_id = Column(String, nullable=True)
    details = Column(JSONB, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String, nullable=True)


class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(String, nullable=False, index=True)
    status = Column(Enum(StatusEnum), nullable=False, default=StatusEnum.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    files = relationship("IngestionFile", back_populates="job")
    errors = relationship("ProcessingError", back_populates="job")


class IngestionFile(Base):
    __tablename__ = "ingestion_files"
    __table_args__ = (UniqueConstraint("job_id", "file_hash", name="_job_hash_uc"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("ingestion_jobs.id"), nullable=False)
    file_path = Column(String, nullable=False)
    status = Column(Enum(StatusEnum), nullable=False, default=StatusEnum.PENDING)
    file_hash = Column(String, nullable=True, index=True)
    file_metadata = Column("metadata", JSONB, nullable=True)

    job = relationship("IngestionJob", back_populates="files")
    error = relationship("ProcessingError", back_populates="file", uselist=False)


class ProcessingError(Base):
    __tablename__ = "processing_errors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("ingestion_jobs.id"), nullable=False)
    file_id = Column(
        UUID(as_uuid=True), ForeignKey("ingestion_files.id"), nullable=False
    )
    error_message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    job = relationship("IngestionJob", back_populates="errors")
    file = relationship("IngestionFile", back_populates="error")
