"""Candidate model"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base

if TYPE_CHECKING:
    from .availability import Availability
    from .document import Document
    from .ontology import Decision


class Candidate(Base):
    """Candidate information table"""

    __tablename__ = "candidates"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4, server_default="gen_random_uuid()"
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True, unique=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="candidate")
    availability: Mapped[List["Availability"]] = relationship(
        "Availability", back_populates="candidate", cascade="all, delete-orphan"
    )
    decisions: Mapped[List["Decision"]] = relationship(
        "Decision", back_populates="candidate", cascade="all, delete-orphan"
    )
