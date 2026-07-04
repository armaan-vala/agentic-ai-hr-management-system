"""Company announcements — admin posts, everyone reads."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.announcement import Announcement
from app.models.user import Role, User
from app.services import announcements as svc
from app.services.llm_util import json_completion

router = APIRouter(prefix="/announcements", tags=["announcements"])


class AnnouncementIn(BaseModel):
    title: str
    body: str
    email_everyone: bool = False


class AnnouncementOut(BaseModel):
    id: str
    title: str
    body: str
    created_at: str


class PostResult(AnnouncementOut):
    email_result: dict | None = None


@router.get("", response_model=list[AnnouncementOut])
async def list_announcements(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[AnnouncementOut]:
    rows = (
        await db.execute(
            select(Announcement)
            .where(Announcement.company_id == user.company_id)
            .order_by(Announcement.created_at.desc())
            .limit(100)
        )
    ).scalars().all()
    return [
        AnnouncementOut(
            id=str(a.id), title=a.title, body=a.body,
            created_at=a.created_at.isoformat() if a.created_at else "",
        )
        for a in rows
    ]


class DraftIn(BaseModel):
    topic: str


@router.post("/draft")
async def draft_announcement(
    body: DraftIn, user: User = Depends(get_current_user)
) -> dict:
    """AI-draft an announcement (title + body) from a short topic."""
    if user.role != Role.admin:
        raise HTTPException(status_code=403, detail="Admin only")
    result = await json_completion(
        "You are an internal-comms writer. Draft a company announcement from the topic. "
        "Return JSON: {title (short), body (2-4 warm, clear sentences)}.",
        f"Topic: {body.topic}",
    )
    if not result:
        return {"title": body.topic, "body": ""}
    return {"title": result.get("title", body.topic), "body": result.get("body", "")}


@router.post("", response_model=PostResult)
async def post_announcement(
    body: AnnouncementIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PostResult:
    if user.role != Role.admin:
        raise HTTPException(status_code=403, detail="Admin only")
    ann = await svc.create_announcement(
        db, company_id=user.company_id, author_id=user.id, title=body.title, body=body.body
    )
    email_result = None
    if body.email_everyone:
        email_result = await svc.email_everyone(db, author=user, title=body.title, body=body.body)
    return PostResult(
        id=str(ann.id), title=ann.title, body=ann.body,
        created_at=ann.created_at.isoformat() if ann.created_at else "",
        email_result=email_result,
    )
