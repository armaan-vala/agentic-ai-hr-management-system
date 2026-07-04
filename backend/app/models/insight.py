"""
Copilot insights — proactively surfaced items for the admin.

Design note (reliability): the FACTS in each insight come from deterministic DB
queries, never from the LLM. The LLM only writes the natural-language digest,
grounded strictly in these facts. So numbers are always trustworthy.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Insight(Base):
    __tablename__ = "insights"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), index=True
    )
    type: Mapped[str] = mapped_column(String(50))          # pending_leaves, not_clocked_in, ...
    severity: Mapped[str] = mapped_column(String(20))      # info | warning | critical
    title: Mapped[str] = mapped_column(String(300))
    detail: Mapped[str] = mapped_column(Text, default="")
    action_path: Mapped[str] = mapped_column(String(80), default="")  # UI route to act on it
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class CopilotDigest(Base):
    __tablename__ = "copilot_digests"

    # One current digest per company (upserted each run).
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), primary_key=True
    )
    summary: Mapped[str] = mapped_column(Text, default="")
    grounded: Mapped[bool] = mapped_column(default=True)   # False if LLM fallback was used
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
