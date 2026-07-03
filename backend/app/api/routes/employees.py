"""Admin employee management."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.integrations import supabase_admin
from app.models.user import Role, User

router = APIRouter(prefix="/employees", tags=["employees"])


def _require_admin(user: User) -> None:
    if user.role != Role.admin:
        raise HTTPException(status_code=403, detail="Admin only")


class NewEmployee(BaseModel):
    email: EmailStr
    full_name: str = ""


class EmployeeOut(BaseModel):
    id: str
    email: str
    full_name: str
    role: str


class CreatedEmployee(EmployeeOut):
    temp_password: str
    note: str


@router.get("", response_model=list[EmployeeOut])
async def list_employees(
    admin: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[EmployeeOut]:
    _require_admin(admin)
    rows = (
        await db.execute(
            select(User).where(User.company_id == admin.company_id).order_by(User.email)
        )
    ).scalars().all()
    return [
        EmployeeOut(id=str(u.id), email=u.email, full_name=u.full_name, role=u.role.value)
        for u in rows
    ]


@router.post("", response_model=CreatedEmployee)
async def add_employee(
    body: NewEmployee,
    admin: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CreatedEmployee:
    """Create a Supabase login + our User row for a new employee in the admin's company."""
    _require_admin(admin)

    existing = (
        await db.execute(select(User).where(User.email == body.email))
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail="Email already exists")

    password = supabase_admin.generate_password()
    auth_id = await supabase_admin.create_auth_user(body.email, password)

    user = User(
        id=uuid.UUID(auth_id),
        company_id=admin.company_id,
        email=body.email,
        full_name=body.full_name,
        role=Role.employee,
    )
    db.add(user)
    await db.commit()

    return CreatedEmployee(
        id=auth_id,
        email=body.email,
        full_name=body.full_name,
        role=Role.employee.value,
        temp_password=password,
        note="Share these credentials with the employee. "
        "A welcome email via their manager's Gmail can be sent once Google is connected.",
    )
