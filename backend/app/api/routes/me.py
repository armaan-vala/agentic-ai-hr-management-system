"""Current-user info + profile update."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User

router = APIRouter(tags=["me"])


class MeOut(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    company_id: str


class ProfileUpdate(BaseModel):
    full_name: str


def _out(user: User) -> MeOut:
    return MeOut(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        company_id=str(user.company_id),
    )


@router.get("/me", response_model=MeOut)
async def me(user: User = Depends(get_current_user)) -> MeOut:
    return _out(user)


@router.patch("/me/profile", response_model=MeOut)
async def update_profile(
    body: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MeOut:
    user.full_name = body.full_name.strip()
    await db.commit()
    await db.refresh(user)
    return _out(user)
