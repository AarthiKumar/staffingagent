"""Upload job tracking model for async CV processing"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class UploadStatus(str, Enum):
    """Upload job status"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REQUIRES_INPUT = "requires_input"  # Missing required fields


class UploadJob(Base):
    """Track async CV upload and processing jobs"""

    __tablename__ = "upload_jobs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    # Job metadata
    filename: Mapped[str] = mapped_column(String(500))
    agent_id: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(50), default=UploadStatus.QUEUED)

    # Progress tracking
    progress: Mapped[int] = mapped_column(default=0)  # 0-100
    current_step: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Results
    document_id: Mapped[Optional[uuid.UUID]] = mapped_column(nullable=True)
    candidate_id: Mapped[Optional[uuid.UUID]] = mapped_column(nullable=True)

    # Missing fields that require user input
    missing_fields: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # ["name", "email", "phone"]

    # Error information
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Processing metadata
    sections_count: Mapped[int] = mapped_column(default=0)
    embeddings_count: Mapped[int] = mapped_column(default=0)

    # Merge proposal for duplicate candidates
    merge_proposal: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    requires_approval: Mapped[bool] = mapped_column(default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    def to_dict(self):
        """Convert to dictionary for API response"""
        return {
            "id": str(self.id),
            "filename": self.filename,
            "agent_id": self.agent_id,
            "status": self.status,
            "progress": self.progress,
            "current_step": self.current_step,
            "document_id": str(self.document_id) if self.document_id else None,
            "candidate_id": str(self.candidate_id) if self.candidate_id else None,
            "missing_fields": self.missing_fields,
            "error_message": self.error_message,
            "sections_count": self.sections_count,
            "embeddings_count": self.embeddings_count,
            "merge_proposal": self.merge_proposal,
            "requires_approval": self.requires_approval,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
