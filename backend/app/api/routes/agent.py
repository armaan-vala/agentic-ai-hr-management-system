"""AI Agent Console — see what the agents have done / want to do."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.agent_action import AgentAction
from app.models.user import Role, User

router = APIRouter(prefix="/agent", tags=["agent"])


class ActionOut(BaseModel):
    id: str
    tool_name: str
    summary: str
    args: dict
    status: str
    result: dict | None
    created_at: str
    decided_at: str | None


@router.get("/actions", response_model=list[ActionOut])
async def list_actions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ActionOut]:
    """Admins see all company actions; employees see only their own."""
    q = select(AgentAction).where(AgentAction.company_id == user.company_id)
    if user.role != Role.admin:
        q = q.where(AgentAction.user_id == user.id)
    q = q.order_by(AgentAction.created_at.desc()).limit(200)

    rows = (await db.execute(q)).scalars().all()
    return [
        ActionOut(
            id=str(a.id),
            tool_name=a.tool_name,
            summary=a.summary,
            args=a.args or {},
            status=a.status.value,
            result=a.result,
            created_at=a.created_at.isoformat() if a.created_at else "",
            decided_at=a.decided_at.isoformat() if a.decided_at else None,
        )
        for a in rows
    ]
