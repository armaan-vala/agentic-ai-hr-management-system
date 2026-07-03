"""Helpdesk tickets — employee raises, admin resolves."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.ticket import Ticket, TicketStatus
from app.models.user import Role, User

router = APIRouter(prefix="/tickets", tags=["tickets"])


class TicketIn(BaseModel):
    subject: str
    message: str


class TicketOut(BaseModel):
    id: str
    raised_by: str
    subject: str
    message: str
    status: str
    admin_response: str
    created_at: str


class ResolveIn(BaseModel):
    response: str = ""


def _out(t: Ticket, name: str) -> TicketOut:
    return TicketOut(
        id=str(t.id), raised_by=name, subject=t.subject, message=t.message,
        status=t.status.value, admin_response=t.admin_response,
        created_at=t.created_at.isoformat() if t.created_at else "",
    )


@router.post("", response_model=TicketOut)
async def create_ticket(
    body: TicketIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TicketOut:
    t = Ticket(company_id=user.company_id, user_id=user.id, subject=body.subject, message=body.message)
    db.add(t)
    await db.commit()
    await db.refresh(t)
    return _out(t, user.full_name or user.email)


@router.get("/mine", response_model=list[TicketOut])
async def my_tickets(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[TicketOut]:
    rows = (
        await db.execute(
            select(Ticket).where(Ticket.user_id == user.id).order_by(Ticket.created_at.desc())
        )
    ).scalars().all()
    name = user.full_name or user.email
    return [_out(t, name) for t in rows]


@router.get("", response_model=list[TicketOut])
async def all_tickets(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[TicketOut]:
    if user.role != Role.admin:
        raise HTTPException(status_code=403, detail="Admin only")
    rows = (
        await db.execute(
            select(Ticket, User)
            .join(User, Ticket.user_id == User.id)
            .where(Ticket.company_id == user.company_id)
            .order_by(Ticket.status, Ticket.created_at.desc())
        )
    ).all()
    return [_out(t, u.full_name or u.email) for t, u in rows]


@router.post("/{ticket_id}/resolve", response_model=TicketOut)
async def resolve_ticket(
    ticket_id: uuid.UUID,
    body: ResolveIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TicketOut:
    if user.role != Role.admin:
        raise HTTPException(status_code=403, detail="Admin only")
    t = await db.get(Ticket, ticket_id)
    if t is None or t.company_id != user.company_id:
        raise HTTPException(status_code=404, detail="Not found")
    t.status = TicketStatus.resolved
    t.admin_response = body.response
    t.resolved_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(t)
    owner = await db.get(User, t.user_id)
    return _out(t, owner.full_name if owner else "")
