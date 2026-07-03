"""Per-employee salary structure set by the admin."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class SalaryStructure(Base):
    __tablename__ = "salary_structures"

    # One structure per employee.
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), index=True
    )
    # Monthly amounts in whole currency units.
    basic: Mapped[int] = mapped_column(Integer, default=0)
    hra: Mapped[int] = mapped_column(Integer, default=0)
    allowances: Mapped[int] = mapped_column(Integer, default=0)
    deductions: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String(8), default="INR")

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    @property
    def gross(self) -> int:
        return self.basic + self.hra + self.allowances

    @property
    def net(self) -> int:
        return self.gross - self.deductions
