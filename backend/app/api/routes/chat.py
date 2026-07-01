"""Chat endpoint — talk to the agentic assistant."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.runtime import run_agent
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User

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
