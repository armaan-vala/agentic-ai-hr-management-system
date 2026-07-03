"""Dashboard summary stats for the home page."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.agent_action import AgentAction
from app.models.announcement import Announcement
from app.models.company import Company
from app.models.leave_request import LeaveRequest, LeaveStatus
from app.models.policy import Policy
from app.models.user import Role, User

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


class RecentAnnouncement(BaseModel):
    title: str
    created_at: str


class DashboardOut(BaseModel):
    role: str
    greeting_name: str
    # employee-focused
    leave_balance: int | None = None
    my_pending_leaves: int | None = None
    # admin-focused
    employee_count: int | None = None
    pending_leaves: int | None = None
    policy_count: int | None = None
    agent_actions: int | None = None
    recent_announcements: list[RecentAnnouncement] = []


async def _count(db: AsyncSession, stmt) -> int:
    return (await db.execute(stmt)).scalar_one()


@router.get("", response_model=DashboardOut)
async def dashboard(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> DashboardOut:
    cid = user.company_id

    recents = (
        await db.execute(
            select(Announcement)
            .where(Announcement.company_id == cid)
            .order_by(Announcement.created_at.desc())
            .limit(5)
        )
    ).scalars().all()
    recent_announcements = [
        RecentAnnouncement(title=a.title, created_at=a.created_at.isoformat() if a.created_at else "")
        for a in recents
    ]

    out = DashboardOut(
        role=user.role.value,
        greeting_name=user.full_name or user.email.split("@")[0],
        recent_announcements=recent_announcements,
    )

    if user.role == Role.admin:
        company = await db.get(Company, cid)
        out.employee_count = await _count(
            db, select(func.count(User.id)).where(User.company_id == cid)
        )
        out.pending_leaves = await _count(
            db,
            select(func.count(LeaveRequest.id)).where(
                LeaveRequest.company_id == cid, LeaveRequest.status == LeaveStatus.pending
            ),
        )
        out.policy_count = await _count(
            db, select(func.count(Policy.id)).where(Policy.company_id == cid)
        )
        out.agent_actions = await _count(
            db, select(func.count(AgentAction.id)).where(AgentAction.company_id == cid)
        )
    else:
        company = await db.get(Company, cid)
        limit = company.annual_leave_limit if company else 0
        out.leave_balance = limit - user.leaves_used
        out.my_pending_leaves = await _count(
            db,
            select(func.count(LeaveRequest.id)).where(
                LeaveRequest.user_id == user.id, LeaveRequest.status == LeaveStatus.pending
            ),
        )

    return out
