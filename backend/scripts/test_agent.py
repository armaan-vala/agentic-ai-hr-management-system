"""
Dev-only end-to-end test of the agent loop (no HTTP / no auth).

Seeds a test company + employee, then asks the agent a question that should make
it call the get_leave_balance tool and answer from real DB data.

Run inside the backend container:
    docker compose exec -T backend python -m scripts.test_agent
"""
from __future__ import annotations

import asyncio
import uuid

from sqlalchemy import select

from app.agent.runtime import run_agent
from app.db.session import SessionLocal
from app.models.company import Company
from app.models.user import Role, User

# Deterministic ids so re-runs reuse the same rows.
TEST_COMPANY_ID = uuid.uuid5(uuid.NAMESPACE_DNS, "talentos-test-company")
TEST_USER_ID = uuid.uuid5(uuid.NAMESPACE_DNS, "talentos-test-user")


async def seed(db) -> User:
    company = await db.get(Company, TEST_COMPANY_ID)
    if company is None:
        company = Company(id=TEST_COMPANY_ID, name="Test Co", annual_leave_limit=12)
        db.add(company)
        await db.flush()

    user = await db.get(User, TEST_USER_ID)
    if user is None:
        user = User(
            id=TEST_USER_ID,
            company_id=TEST_COMPANY_ID,
            email="rahul@testco.com",
            full_name="Rahul",
            role=Role.employee,
            leaves_used=3,  # so balance should be 12 - 3 = 9
        )
        db.add(user)
    else:
        user.leaves_used = 3
    await db.commit()
    await db.refresh(user)
    return user


async def main() -> None:
    async with SessionLocal() as db:
        user = await seed(db)
        print(f"User: {user.full_name} | used={user.leaves_used}\n")

        result = await run_agent(
            user=user,
            db=db,
            message="Hey, how many leave days do I have left this year?",
        )
        print("=== AGENT REPLY ===")
        print(result.reply)
        print("\n=== TOOL TRACE ===")
        for step in result.trace:
            print(step)


if __name__ == "__main__":
    asyncio.run(main())
