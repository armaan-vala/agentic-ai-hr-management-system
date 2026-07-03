"""
AgentAction — a side-effecting action the agent wants to take, pending human approval.

This table powers the "AI Agent Console" (see + approve/reject what agents do) and
doubles as an audit log of every action tool invocation and its outcome.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class ActionStatus(str, enum.Enum):
    pending = "pending"     # proposed by agent, awaiting approval
    rejected = "rejected"
    executed = "executed"   # approved and ran successfully
    failed = "failed"       # approved but the tool errored


class AgentAction(Base):
    __tablename__ = "agent_actions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), index=True
    )
    # The user the action is performed on behalf of (the one chatting).
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    tool_name: Mapped[str] = mapped_column(String(100))
    summary: Mapped[str] = mapped_column(String(500))
    args: Mapped[dict] = mapped_column(JSONB, default=dict)
    status: Mapped[ActionStatus] = mapped_column(
        Enum(ActionStatus, name="action_status"), default=ActionStatus.pending, index=True
    )
    result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    decided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
