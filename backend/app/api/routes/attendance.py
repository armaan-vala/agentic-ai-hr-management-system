"""Attendance — clock in/out, my timesheet, admin team view."""
from __future__ import annotations

from datetime import date as date_type
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.attendance import AttendanceRecord
from app.models.user import Role, User
from app.services import attendance as svc

router = APIRouter(prefix="/attendance", tags=["attendance"])


class TodayOut(BaseModel):
    status: str
    clock_in: str | None
    clock_out: str | None
    hours: float


class DayRow(BaseModel):
    date: str
    clock_in: str | None
    clock_out: str | None
    hours: float
    status: str


class TeamRow(BaseModel):
    user_id: str
    name: str
    status: str
    clock_in: str | None
    hours: float


@router.get("/today", response_model=TodayOut)
async def today(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> TodayOut:
    return TodayOut(**await svc.today_status(db, user))


@router.post("/clock-in", response_model=dict)
async def clock_in(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> dict:
    return await svc.clock_in(db, user)


@router.post("/clock-out", response_model=dict)
async def clock_out(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> dict:
    return await svc.clock_out(db, user)


@router.get("/mine", response_model=list[DayRow])
async def mine(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[DayRow]:
    rows = (
        await db.execute(
            select(AttendanceRecord)
            .where(AttendanceRecord.user_id == user.id)
            .order_by(AttendanceRecord.date.desc())
            .limit(30)
        )
    ).scalars().all()
    return [
        DayRow(
            date=r.date.isoformat(),
            clock_in=r.clock_in.isoformat() if r.clock_in else None,
            clock_out=r.clock_out.isoformat() if r.clock_out else None,
            hours=r.hours,
            status=r.status,
        )
        for r in rows
    ]


@router.get("/team", response_model=list[TeamRow])
async def team(
    date: str | None = None,
    admin: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[TeamRow]:
    if admin.role != Role.admin:
        raise HTTPException(status_code=403, detail="Admin only")
    day = date_type.fromisoformat(date) if date else datetime.now(timezone.utc).date()
    rows = (
        await db.execute(
            select(User, AttendanceRecord)
            .outerjoin(
                AttendanceRecord,
                (AttendanceRecord.user_id == User.id) & (AttendanceRecord.date == day),
            )
            .where(User.company_id == admin.company_id)
            .order_by(User.email)
        )
    ).all()
    out = []
    for u, r in rows:
        out.append(
            TeamRow(
                user_id=str(u.id),
                name=u.full_name or u.email,
                status=r.status if r else "not_started",
                clock_in=r.clock_in.isoformat() if r and r.clock_in else None,
                hours=r.hours if r else 0.0,
            )
        )
    return out
