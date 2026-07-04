"""Personal nudges for the current user."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services import nudges as svc

router = APIRouter(prefix="/nudges", tags=["nudges"])


class Nudge(BaseModel):
    icon: str
    text: str
    action_path: str


@router.get("", response_model=list[Nudge])
async def my_nudges(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[Nudge]:
    return [Nudge(**n) for n in await svc.personal_nudges(db, user)]
