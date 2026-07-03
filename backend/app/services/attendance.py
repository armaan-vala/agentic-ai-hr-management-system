"""Clock-in/out logic shared by REST endpoints and agent tools."""
from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance import AttendanceRecord
from app.models.user import User


async def _today_record(db: AsyncSession, user: User) -> AttendanceRecord | None:
    today = datetime.now(timezone.utc).date()
    return (
        await db.execute(
            select(AttendanceRecord).where(
                AttendanceRecord.user_id == user.id, AttendanceRecord.date == today
            )
        )
    ).scalar_one_or_none()


def _status(rec: AttendanceRecord | None) -> dict:
    if rec is None:
        return {"status": "not_started", "clock_in": None, "clock_out": None, "hours": 0.0}
    return {
        "status": rec.status,
        "clock_in": rec.clock_in.isoformat() if rec.clock_in else None,
        "clock_out": rec.clock_out.isoformat() if rec.clock_out else None,
        "hours": rec.hours,
    }


async def today_status(db: AsyncSession, user: User) -> dict:
    return _status(await _today_record(db, user))


async def clock_in(db: AsyncSession, user: User) -> dict:
    now = datetime.now(timezone.utc)
    rec = await _today_record(db, user)
    if rec and rec.clock_in:
        return {"ok": False, "message": "Already clocked in today.", **_status(rec)}
    if rec is None:
        rec = AttendanceRecord(company_id=user.company_id, user_id=user.id, date=now.date())
        db.add(rec)
    rec.clock_in = now
    await db.commit()
    await db.refresh(rec)
    return {"ok": True, "message": "Clocked in.", **_status(rec)}


async def clock_out(db: AsyncSession, user: User) -> dict:
    now = datetime.now(timezone.utc)
    rec = await _today_record(db, user)
    if rec is None or not rec.clock_in:
        return {"ok": False, "message": "You haven't clocked in yet today."}
    if rec.clock_out:
        return {"ok": False, "message": "Already clocked out today.", **_status(rec)}
    rec.clock_out = now
    await db.commit()
    await db.refresh(rec)
    return {"ok": True, "message": "Clocked out.", **_status(rec)}
