"""Embedding model with pgvector support"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base

if TYPE_CHECKING:
    from .document import Document
    from .section import Section


class Embedding(Base):
    """Embedding vectors table"""

    __tablename__ = "embeddings"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4, server_default="gen_random_uuid()"
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    section_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("sections.id", ondelete="CASCADE"), nullable=True, index=True
    )
    agent_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    model: Mapped[str] = mapped_column(String(255), nullable=False)
    dim: Mapped[int] = mapped_column(Integer, nullable=False)
    vector: Mapped[list[float]] = mapped_column(Vector(None), nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="embeddings")
    section: Mapped[Optional["Section"]] = relationship("Section", back_populates="embeddings")
