"""Payroll — admin sets salary, generates & releases payslips; employees view theirs."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.payslip import Payslip, PayslipStatus
from app.models.salary_structure import SalaryStructure
from app.models.user import Role, User

router = APIRouter(prefix="/payroll", tags=["payroll"])


def _require_admin(user: User) -> None:
    if user.role != Role.admin:
        raise HTTPException(status_code=403, detail="Admin only")


# ---------- salary structures ----------
class StructureIn(BaseModel):
    basic: int = 0
    hra: int = 0
    allowances: int = 0
    deductions: int = 0
    currency: str = "INR"


class StructureRow(BaseModel):
    user_id: str
    name: str
    email: str
    basic: int
    hra: int
    allowances: int
    deductions: int
    gross: int
    net: int
    currency: str
    has_structure: bool


@router.get("/structures", response_model=list[StructureRow])
async def list_structures(
    admin: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[StructureRow]:
    _require_admin(admin)
    rows = (
        await db.execute(
            select(User, SalaryStructure)
            .outerjoin(SalaryStructure, SalaryStructure.user_id == User.id)
            .where(User.company_id == admin.company_id)
            .order_by(User.email)
        )
    ).all()
    out = []
    for u, s in rows:
        out.append(
            StructureRow(
                user_id=str(u.id),
                name=u.full_name or u.email,
                email=u.email,
                basic=s.basic if s else 0,
                hra=s.hra if s else 0,
                allowances=s.allowances if s else 0,
                deductions=s.deductions if s else 0,
                gross=s.gross if s else 0,
                net=s.net if s else 0,
                currency=s.currency if s else "INR",
                has_structure=s is not None,
            )
        )
    return out


@router.put("/structure/{user_id}")
async def set_structure(
    user_id: uuid.UUID,
    body: StructureIn,
    admin: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    _require_admin(admin)
    target = await db.get(User, user_id)
    if target is None or target.company_id != admin.company_id:
        raise HTTPException(status_code=404, detail="Employee not found")

    s = await db.get(SalaryStructure, user_id)
    if s is None:
        s = SalaryStructure(user_id=user_id, company_id=admin.company_id)
        db.add(s)
    s.basic, s.hra, s.allowances, s.deductions, s.currency = (
        body.basic, body.hra, body.allowances, body.deductions, body.currency
    )
    await db.commit()
    return {"ok": True, "gross": s.gross, "net": s.net}


# ---------- payslip generation ----------
class MonthIn(BaseModel):
    month: str  # "YYYY-MM"


class PayslipOut(BaseModel):
    id: str
    user_id: str
    name: str
    month: str
    basic: int
    hra: int
    allowances: int
    deductions: int
    gross: int
    net: int
    currency: str
    status: str


def _slip_out(p: Payslip, name: str) -> PayslipOut:
    return PayslipOut(
        id=str(p.id), user_id=str(p.user_id), name=name, month=p.month,
        basic=p.basic, hra=p.hra, allowances=p.allowances, deductions=p.deductions,
        gross=p.gross, net=p.net, currency=p.currency, status=p.status.value,
    )


@router.post("/generate")
async def generate(
    body: MonthIn,
    admin: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create draft payslips for all employees that have a salary structure."""
    _require_admin(admin)
    structures = (
        await db.execute(
            select(SalaryStructure).where(SalaryStructure.company_id == admin.company_id)
        )
    ).scalars().all()

    created, updated = 0, 0
    for s in structures:
        existing = (
            await db.execute(
                select(Payslip).where(Payslip.user_id == s.user_id, Payslip.month == body.month)
            )
        ).scalar_one_or_none()
        if existing and existing.status == PayslipStatus.released:
            continue  # don't overwrite released payslips
        if existing is None:
            existing = Payslip(company_id=admin.company_id, user_id=s.user_id, month=body.month)
            db.add(existing)
            created += 1
        else:
            updated += 1
        existing.basic, existing.hra, existing.allowances, existing.deductions = (
            s.basic, s.hra, s.allowances, s.deductions
        )
        existing.gross, existing.net, existing.currency = s.gross, s.net, s.currency
        existing.status = PayslipStatus.draft
    await db.commit()
    return {"month": body.month, "created": created, "updated": updated}


@router.post("/release")
async def release(
    body: MonthIn,
    admin: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    _require_admin(admin)
    slips = (
        await db.execute(
            select(Payslip).where(
                Payslip.company_id == admin.company_id,
                Payslip.month == body.month,
                Payslip.status == PayslipStatus.draft,
            )
        )
    ).scalars().all()
    for p in slips:
        p.status = PayslipStatus.released
        p.released_at = datetime.now(timezone.utc)
    await db.commit()
    return {"month": body.month, "released": len(slips)}


@router.get("/payslips", response_model=list[PayslipOut])
async def admin_payslips(
    month: str,
    admin: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[PayslipOut]:
    _require_admin(admin)
    rows = (
        await db.execute(
            select(Payslip, User)
            .join(User, Payslip.user_id == User.id)
            .where(Payslip.company_id == admin.company_id, Payslip.month == month)
            .order_by(User.email)
        )
    ).all()
    return [_slip_out(p, u.full_name or u.email) for p, u in rows]
