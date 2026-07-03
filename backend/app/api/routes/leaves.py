"""Leave REST endpoints (used by the UI forms; the agent uses the tools instead)."""
from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.company import Company
from app.models.leave_request import LeaveRequest, LeaveStatus
from app.models.user import Role, User

router = APIRouter(prefix="/leaves", tags=["leaves"])


class LeaveOut(BaseModel):
    id: str
    employee: str
    type: str
    start_date: str
    end_date: str
    days: int
    reason: str
    status: str


class ApplyLeave(BaseModel):
    leave_type: str
    start_date: date
    end_date: date
    reason: str = ""


class BalanceOut(BaseModel):
    annual_limit: int
    used: int
    balance: int


def _to_out(lr: LeaveRequest, name: str) -> LeaveOut:
    return LeaveOut(
        id=str(lr.id),
        employee=name,
        type=lr.leave_type,
        start_date=lr.start_date.isoformat(),
        end_date=lr.end_date.isoformat(),
        days=lr.days,
        reason=lr.reason,
        status=lr.status.value,
    )


@router.get("/balance", response_model=BalanceOut)
async def my_balance(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> BalanceOut:
    company = await db.get(Company, user.company_id)
    limit = company.annual_leave_limit if company else 0
    return BalanceOut(annual_limit=limit, used=user.leaves_used, balance=limit - user.leaves_used)


@router.get("/mine", response_model=list[LeaveOut])
async def my_leaves(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[LeaveOut]:
    rows = (
        await db.execute(
            select(LeaveRequest)
            .where(LeaveRequest.user_id == user.id)
            .order_by(LeaveRequest.created_at.desc())
        )
    ).scalars().all()
    return [_to_out(lr, user.full_name or user.email) for lr in rows]


@router.post("/", response_model=LeaveOut)
async def apply_leave(
    body: ApplyLeave,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LeaveOut:
    if body.end_date < body.start_date:
        raise HTTPException(status_code=400, detail="end_date before start_date")
    days = (body.end_date - body.start_date).days + 1
    lr = LeaveRequest(
        company_id=user.company_id,
        user_id=user.id,
        leave_type=body.leave_type,
        start_date=body.start_date,
        end_date=body.end_date,
        days=days,
        reason=body.reason,
    )
    db.add(lr)
    await db.commit()
    await db.refresh(lr)
    return _to_out(lr, user.full_name or user.email)


@router.get("/pending", response_model=list[LeaveOut])
async def pending_leaves(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[LeaveOut]:
    if user.role != Role.admin:
        raise HTTPException(status_code=403, detail="Admin only")
    rows = (
        await db.execute(
            select(LeaveRequest, User)
            .join(User, LeaveRequest.user_id == User.id)
            .where(
                LeaveRequest.company_id == user.company_id,
                LeaveRequest.status == LeaveStatus.pending,
            )
            .order_by(LeaveRequest.created_at.asc())
        )
    ).all()
    return [_to_out(lr, u.full_name or u.email) for lr, u in rows]


class Decision(BaseModel):
    decision: str  # approve | reject


@router.post("/{leave_id}/decision", response_model=LeaveOut)
async def decide(
    leave_id: uuid.UUID,
    body: Decision,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LeaveOut:
    if user.role != Role.admin:
        raise HTTPException(status_code=403, detail="Admin only")
    lr = await db.get(LeaveRequest, leave_id)
    if lr is None or lr.company_id != user.company_id:
        raise HTTPException(status_code=404, detail="Not found")
    if lr.status != LeaveStatus.pending:
        raise HTTPException(status_code=400, detail=f"Already {lr.status.value}")

    employee = await db.get(User, lr.user_id)
    if body.decision == "approve":
        lr.status = LeaveStatus.approved
        if employee is not None:
            employee.leaves_used += lr.days
    else:
        lr.status = LeaveStatus.rejected
    await db.commit()
    await db.refresh(lr)
    return _to_out(lr, employee.full_name if employee else "")
