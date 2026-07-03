"""Chat endpoint — talk to the agentic assistant."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.runtime import run_agent
from app.agent.tools import ToolContext, registry
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.agent_action import ActionStatus, AgentAction
from app.models.user import Role, User

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []


class ChatResponse(BaseModel):
    reply: str
    trace: list[dict] = []
    pending_approval: dict | None = None


@router.post("/message", response_model=ChatResponse)
async def chat_message(
    body: ChatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    result = await run_agent(
        user=user,
        db=db,
        message=body.message,
        history=[m.model_dump() for m in body.history],
    )
    return ChatResponse(
        reply=result.reply,
        trace=result.trace,
        pending_approval=result.pending_approval,
    )


class ApprovalRequest(BaseModel):
    action_id: uuid.UUID
    decision: Literal["approve", "reject"]


class ApprovalResponse(BaseModel):
    status: str
    reply: str
    result: dict | None = None


@router.post("/approve", response_model=ApprovalResponse)
async def approve_action(
    body: ApprovalRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApprovalResponse:
    """Approve or reject a pending agent action (human-in-the-loop)."""
    action = await db.get(AgentAction, body.action_id)
    if action is None or action.company_id != user.company_id:
        raise HTTPException(status_code=404, detail="Action not found")
    # Only the requester or a company admin may decide.
    if user.role != Role.admin and action.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed to decide this action")
    if action.status != ActionStatus.pending:
        raise HTTPException(status_code=400, detail=f"Already {action.status.value}")

    action.decided_at = datetime.now(timezone.utc)

    if body.decision == "reject":
        action.status = ActionStatus.rejected
        await db.commit()
        return ApprovalResponse(status="rejected", reply="Okay, I've cancelled that.")

    # Approved → execute the tool on behalf of the original requester.
    tool = registry.get(action.tool_name)
    requester = await db.get(User, action.user_id)
    if tool is None or requester is None:
        action.status = ActionStatus.failed
        action.result = {"error": "tool or requester missing"}
        await db.commit()
        raise HTTPException(status_code=500, detail="Cannot execute action")

    ctx = ToolContext(user=requester, db=db)
    try:
        result = await tool.handler(ctx, **action.args)
        action.status = ActionStatus.executed
        action.result = result
        reply = f"Done — {action.summary.lower()}."
    except Exception as exc:  # noqa: BLE001 — record any failure for the console
        action.status = ActionStatus.failed
        action.result = {"error": str(exc)}
        reply = f"That failed: {exc}"

    await db.commit()
    return ApprovalResponse(status=action.status.value, reply=reply, result=action.result)
