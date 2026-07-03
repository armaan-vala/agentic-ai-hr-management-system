"""Company settings (admin editable)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.company import Company
from app.models.user import Role, User

router = APIRouter(prefix="/company", tags=["company"])


class CompanyOut(BaseModel):
    name: str
    annual_leave_limit: int


class CompanyUpdate(BaseModel):
    name: str
    annual_leave_limit: int


@router.get("", response_model=CompanyOut)
async def get_company(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> CompanyOut:
    c = await db.get(Company, user.company_id)
    return CompanyOut(name=c.name, annual_leave_limit=c.annual_leave_limit)


@router.put("", response_model=CompanyOut)
async def update_company(
    body: CompanyUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CompanyOut:
    if user.role != Role.admin:
        raise HTTPException(status_code=403, detail="Admin only")
    c = await db.get(Company, user.company_id)
    c.name = body.name.strip()
    c.annual_leave_limit = max(0, body.annual_leave_limit)
    await db.commit()
    await db.refresh(c)
    return CompanyOut(name=c.name, annual_leave_limit=c.annual_leave_limit)
