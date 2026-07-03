"""Monthly payslips generated from salary structures."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class PayslipStatus(str, enum.Enum):
    draft = "draft"        # generated, not visible to employee yet
    released = "released"  # visible to employee


class Payslip(Base):
    __tablename__ = "payslips"
    __table_args__ = (UniqueConstraint("user_id", "month", name="uq_payslip_user_month"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    month: Mapped[str] = mapped_column(String(7))  # "YYYY-MM"
    basic: Mapped[int] = mapped_column(Integer)
    hra: Mapped[int] = mapped_column(Integer)
    allowances: Mapped[int] = mapped_column(Integer)
    deductions: Mapped[int] = mapped_column(Integer)
    gross: Mapped[int] = mapped_column(Integer)
    net: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(8), default="INR")
    status: Mapped[PayslipStatus] = mapped_column(
        Enum(PayslipStatus, name="payslip_status"), default=PayslipStatus.draft, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
