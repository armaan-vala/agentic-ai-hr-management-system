"""Employee payslip access (released payslips only)."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.payslip import Payslip, PayslipStatus
from app.models.user import Role, User

router = APIRouter(prefix="/payslips", tags=["payslips"])


class PayslipView(BaseModel):
    id: str
    month: str
    basic: int
    hra: int
    allowances: int
    deductions: int
    gross: int
    net: int
    currency: str
    status: str
    employee_name: str


@router.get("/mine", response_model=list[PayslipView])
async def my_payslips(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[PayslipView]:
    rows = (
        await db.execute(
            select(Payslip)
            .where(Payslip.user_id == user.id, Payslip.status == PayslipStatus.released)
            .order_by(Payslip.month.desc())
        )
    ).scalars().all()
    name = user.full_name or user.email
    return [_view(p, name) for p in rows]


@router.get("/{payslip_id}", response_model=PayslipView)
async def payslip_detail(
    payslip_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PayslipView:
    p = await db.get(Payslip, payslip_id)
    if p is None or p.company_id != user.company_id:
        raise HTTPException(status_code=404, detail="Not found")
    # Employees can only see their own released payslips; admins can see any.
    if user.role != Role.admin and (p.user_id != user.id or p.status != PayslipStatus.released):
        raise HTTPException(status_code=403, detail="Not allowed")
    owner = await db.get(User, p.user_id)
    return _view(p, owner.full_name if owner else "")


def _view(p: Payslip, name: str) -> PayslipView:
    return PayslipView(
        id=str(p.id), month=p.month, basic=p.basic, hra=p.hra, allowances=p.allowances,
        deductions=p.deductions, gross=p.gross, net=p.net, currency=p.currency,
        status=p.status.value, employee_name=name,
    )
