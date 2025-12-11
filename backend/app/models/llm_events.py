"""LLM events and metrics models"""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class LLMEvent(Base):
    """LLM events tracking table"""

    __tablename__ = "llm_events"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4, server_default="gen_random_uuid()"
    )
    ts: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    agent_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    feature: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    model: Mapped[str] = mapped_column(String(255), nullable=False)
    tokens_in: Mapped[int] = mapped_column(Integer, nullable=False)
    tokens_out: Mapped[int] = mapped_column(Integer, nullable=False)
    cost_usd: Mapped[Decimal] = mapped_column(Numeric(10, 6), nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    cache_hit: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    input_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)


class MetricsSearch(Base):
    """Search metrics table"""

    __tablename__ = "metrics_search"

    query_id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4, server_default="gen_random_uuid()"
    )
    ts: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    use_llm: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    p95_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    results_count: Mapped[int] = mapped_column(Integer, nullable=False)
    zero_result: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
