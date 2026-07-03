"""Current-user info for the frontend to route by role."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.security import get_current_user
from app.models.user import User

router = APIRouter(tags=["me"])


class MeOut(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    company_id: str


@router.get("/me", response_model=MeOut)
async def me(user: User = Depends(get_current_user)) -> MeOut:
    return MeOut(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        company_id=str(user.company_id),
    )
