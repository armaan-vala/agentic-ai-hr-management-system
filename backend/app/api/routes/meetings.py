"""Meetings — create Google Calendar events with Meet links."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services import calendar as cal

router = APIRouter(prefix="/meetings", tags=["meetings"])


class MeetingIn(BaseModel):
    title: str
    description: str = ""
    start: str  # ISO 8601, e.g. 2026-07-10T15:00:00
    end: str
    attendees: list[str] = []


class MeetingOut(BaseModel):
    event_id: str | None
    html_link: str | None
    meet_link: str | None


class UpcomingItem(BaseModel):
    summary: str
    start: str | None
    meet_link: str | None
    html_link: str | None


@router.get("/upcoming", response_model=list[UpcomingItem])
async def upcoming(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[UpcomingItem]:
    try:
        items = await cal.upcoming(db, user)
    except cal.NotConnected:
        raise HTTPException(status_code=400, detail="Google not connected")
    return [UpcomingItem(**i) for i in items]


@router.post("", response_model=MeetingOut)
async def create_meeting(
    body: MeetingIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MeetingOut:
    try:
        res = await cal.schedule(
            db, user,
            title=body.title, description=body.description,
            start_iso=body.start, end_iso=body.end, attendees=body.attendees,
        )
    except cal.NotConnected:
        raise HTTPException(status_code=400, detail="Connect Google first")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Calendar error: {exc}")
    return MeetingOut(**res)
