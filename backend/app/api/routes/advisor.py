"""Smart Approvals & Triage endpoints (admin-only, advisory)."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import Role, User
from app.services import advisor

router = APIRouter(prefix="/advisor", tags=["advisor"])


def _admin(user: User) -> None:
    if user.role != Role.admin:
        raise HTTPException(status_code=403, detail="Admin only")


class Recommendation(BaseModel):
    recommendation: str
    reason: str
    confidence: str
    facts: list[str]


class TicketSuggestion(BaseModel):
    category: str
    priority: str
    draft: str
    grounded: bool
    sources: list[str]


@router.get("/leave/{leave_id}", response_model=Recommendation)
async def leave_recommendation(
    leave_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Recommendation:
    _admin(user)
    return Recommendation(**await advisor.recommend_leave(db, leave_id))


@router.get("/expense/{expense_id}", response_model=Recommendation)
async def expense_recommendation(
    expense_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Recommendation:
    _admin(user)
    return Recommendation(**await advisor.recommend_expense(db, expense_id))


@router.get("/ticket/{ticket_id}", response_model=TicketSuggestion)
async def ticket_suggestion(
    ticket_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TicketSuggestion:
    _admin(user)
    return TicketSuggestion(**await advisor.suggest_ticket_reply(db, ticket_id))
