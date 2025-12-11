"""Ontology and Decision models"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base

if TYPE_CHECKING:
    from .candidate import Candidate


class OntologySkill(Base):
    """Canonical skills ontology"""

    __tablename__ = "ontology_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)


class OntologyAlias(Base):
    """Skill aliases mapping"""

    __tablename__ = "ontology_aliases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    alias: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    canonical_skill: Mapped[str] = mapped_column(String(255), nullable=False)


class OntologyCert(Base):
    """Canonical certifications ontology"""

    __tablename__ = "ontology_certs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)


class Decision(Base):
    """Hiring decisions table"""

    __tablename__ = "decisions"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4, server_default="gen_random_uuid()"
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    decision: Mapped[str] = mapped_column(String(50), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    candidate: Mapped["Candidate"] = relationship("Candidate", back_populates="decisions")
