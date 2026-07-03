"""Expense / reimbursement claims — employee submits, admin decides."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.expense import Expense, ExpenseStatus
from app.models.user import Role, User

router = APIRouter(prefix="/expenses", tags=["expenses"])


class ExpenseIn(BaseModel):
    amount: int
    category: str = "other"
    description: str = ""


class ExpenseOut(BaseModel):
    id: str
    employee: str
    amount: int
    currency: str
    category: str
    description: str
    status: str
    created_at: str


class Decision(BaseModel):
    decision: str  # approve | reject


def _out(e: Expense, name: str) -> ExpenseOut:
    return ExpenseOut(
        id=str(e.id), employee=name, amount=e.amount, currency=e.currency,
        category=e.category, description=e.description, status=e.status.value,
        created_at=e.created_at.isoformat() if e.created_at else "",
    )


@router.post("", response_model=ExpenseOut)
async def submit(
    body: ExpenseIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExpenseOut:
    if body.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    e = Expense(
        company_id=user.company_id, user_id=user.id, amount=body.amount,
        category=body.category, description=body.description,
    )
    db.add(e)
    await db.commit()
    await db.refresh(e)
    return _out(e, user.full_name or user.email)


@router.get("/mine", response_model=list[ExpenseOut])
async def mine(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[ExpenseOut]:
    rows = (
        await db.execute(
            select(Expense).where(Expense.user_id == user.id).order_by(Expense.created_at.desc())
        )
    ).scalars().all()
    name = user.full_name or user.email
    return [_out(e, name) for e in rows]


@router.get("/pending", response_model=list[ExpenseOut])
async def pending(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[ExpenseOut]:
    if user.role != Role.admin:
        raise HTTPException(status_code=403, detail="Admin only")
    rows = (
        await db.execute(
            select(Expense, User)
            .join(User, Expense.user_id == User.id)
            .where(Expense.company_id == user.company_id, Expense.status == ExpenseStatus.pending)
            .order_by(Expense.created_at.asc())
        )
    ).all()
    return [_out(e, u.full_name or u.email) for e, u in rows]


@router.post("/{expense_id}/decision", response_model=ExpenseOut)
async def decide(
    expense_id: uuid.UUID,
    body: Decision,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExpenseOut:
    if user.role != Role.admin:
        raise HTTPException(status_code=403, detail="Admin only")
    e = await db.get(Expense, expense_id)
    if e is None or e.company_id != user.company_id:
        raise HTTPException(status_code=404, detail="Not found")
    if e.status != ExpenseStatus.pending:
        raise HTTPException(status_code=400, detail=f"Already {e.status.value}")
    e.status = ExpenseStatus.approved if body.decision == "approve" else ExpenseStatus.rejected
    e.decided_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(e)
    owner = await db.get(User, e.user_id)
    return _out(e, owner.full_name if owner else "")
