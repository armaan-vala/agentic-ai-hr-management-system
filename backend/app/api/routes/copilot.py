"""Proactive HR Copilot — admin-facing insights + digest."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.insight import CopilotDigest, Insight
from app.models.user import Role, User
from app.services import copilot as svc

router = APIRouter(prefix="/copilot", tags=["copilot"])


class InsightOut(BaseModel):
    type: str
    severity: str
    title: str
    detail: str
    action_path: str


class CopilotOut(BaseModel):
    summary: str
    grounded: bool
    generated_at: str | None
    insights: list[InsightOut]


def _require_admin(user: User) -> None:
    if user.role != Role.admin:
        raise HTTPException(status_code=403, detail="Admin only")


@router.get("", response_model=CopilotOut)
async def get_copilot(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> CopilotOut:
    _require_admin(user)
    digest = await db.get(CopilotDigest, user.company_id)
    rows = (
        await db.execute(
            select(Insight)
            .where(Insight.company_id == user.company_id)
            .order_by(Insight.severity.desc(), Insight.created_at.desc())
        )
    ).scalars().all()
    return CopilotOut(
        summary=digest.summary if digest else "Run the copilot to see your briefing.",
        grounded=digest.grounded if digest else True,
        generated_at=digest.generated_at.isoformat() if digest and digest.generated_at else None,
        insights=[
            InsightOut(type=i.type, severity=i.severity, title=i.title, detail=i.detail, action_path=i.action_path)
            for i in rows
        ],
    )


@router.post("/run", response_model=CopilotOut)
async def run_now(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> CopilotOut:
    _require_admin(user)
    res = await svc.run_copilot(db, user.company_id)
    return CopilotOut(
        summary=res["summary"],
        grounded=res["grounded"],
        generated_at=None,
        insights=[InsightOut(**i) for i in res["insights"]],
    )
