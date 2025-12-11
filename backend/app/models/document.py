"""Document and Agent models"""
import uuid
from datetime import datetime
from typing import List

from sqlalchemy import ForeignKey, String, Text, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base


class Agent(Base):
    """Agent configuration table"""

    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    # Relationships
    documents: Mapped[List["Document"]] = relationship("Document", back_populates="agent")


class Document(Base):
    """Document metadata table"""

    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid()
    )
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True, unique=True)
    agent_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("agents.id"), nullable=False, index=True
    )
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(127), nullable=False)
    language: Mapped[str] = mapped_column(String(10), nullable=True)
    ocr: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    # Relationships
    agent: Mapped["Agent"] = relationship("Agent", back_populates="documents")
    sections: Mapped[List["Section"]] = relationship(
        "Section", back_populates="document", cascade="all, delete-orphan"
    )
    embeddings: Mapped[List["Embedding"]] = relationship(
        "Embedding", back_populates="document", cascade="all, delete-orphan"
    )
    candidate: Mapped["Candidate"] = relationship(
        "Candidate", back_populates="document", uselist=False
    )
