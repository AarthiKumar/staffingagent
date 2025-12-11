"""Section model for document chunks"""
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .document import Document
    from .embedding import Embedding


class Section(Base):
    """Document section/chunk table"""

    __tablename__ = "sections"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4, server_default="gen_random_uuid()"
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    start_idx: Mapped[int] = mapped_column(Integer, nullable=True)
    end_idx: Mapped[int] = mapped_column(Integer, nullable=True)

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="sections")
    embeddings: Mapped[list["Embedding"]] = relationship("Embedding", back_populates="section")
