"""People analytics — aggregate stats for the admin dashboard."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.attendance import AttendanceRecord
from app.models.leave_request import LeaveRequest
from app.models.user import Role, User
from app.services import analytics_ai

router = APIRouter(prefix="/analytics", tags=["analytics"])


class Bucket(BaseModel):
    label: str
    value: int


class AnalyticsOut(BaseModel):
    headcount: int
    present_today: int
    pending_leaves: int
    headcount_by_role: list[Bucket]
    leaves_by_status: list[Bucket]
    leaves_by_type: list[Bucket]
    leaves_by_month: list[Bucket]


async def _grouped(db: AsyncSession, column, where) -> dict[str, int]:
    rows = (
        await db.execute(select(column, func.count()).where(where).group_by(column))
    ).all()
    result = {}
    for key, count in rows:
        result[key.value if hasattr(key, "value") else str(key)] = count
    return result


@router.get("", response_model=AnalyticsOut)
async def analytics(
    admin: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> AnalyticsOut:
    if admin.role != Role.admin:
        raise HTTPException(status_code=403, detail="Admin only")
    cid = admin.company_id

    headcount = (
        await db.execute(select(func.count(User.id)).where(User.company_id == cid))
    ).scalar_one()

    today = datetime.now(timezone.utc).date()
    present_today = (
        await db.execute(
            select(func.count(AttendanceRecord.id)).where(
                AttendanceRecord.company_id == cid,
                AttendanceRecord.date == today,
                AttendanceRecord.clock_in.isnot(None),
            )
        )
    ).scalar_one()

    by_role = await _grouped(db, User.role, User.company_id == cid)
    by_status = await _grouped(db, LeaveRequest.status, LeaveRequest.company_id == cid)
    by_type = await _grouped(db, LeaveRequest.leave_type, LeaveRequest.company_id == cid)

    # leaves per month (last 6 months present in data)
    month_rows = (
        await db.execute(
            select(
                func.to_char(LeaveRequest.created_at, "YYYY-MM").label("m"),
                func.count(),
            )
            .where(LeaveRequest.company_id == cid)
            .group_by("m")
            .order_by("m")
        )
    ).all()
    by_month = [Bucket(label=m, value=c) for m, c in month_rows][-6:]

    def buckets(d: dict[str, int]) -> list[Bucket]:
        return [Bucket(label=k, value=v) for k, v in d.items()]

    return AnalyticsOut(
        headcount=headcount,
        present_today=present_today,
        pending_leaves=by_status.get("pending", 0),
        headcount_by_role=buckets(by_role),
        leaves_by_status=buckets(by_status),
        leaves_by_type=buckets(by_type),
        leaves_by_month=by_month,
    )


class AskIn(BaseModel):
    question: str


class AskOut(BaseModel):
    answer: str
    metrics: dict


@router.post("/ask", response_model=AskOut)
async def ask(
    body: AskIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AskOut:
    if user.role != Role.admin:
        raise HTTPException(status_code=403, detail="Admin only")
    res = await analytics_ai.ask(db, user.company_id, body.question)
    return AskOut(**res)
