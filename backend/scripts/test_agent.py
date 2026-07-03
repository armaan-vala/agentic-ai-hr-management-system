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
from app.agent.tools import ToolContext, registry
from app.db.session import SessionLocal
from app.models.agent_action import ActionStatus, AgentAction
from app.models.company import Company
from app.models.leave_request import LeaveRequest
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

        # --- Scenario 1: read tool (no approval) ---
        print("### SCENARIO 1: leave balance (read tool)")
        result = await run_agent(
            user=user,
            db=db,
            message="Hey, how many leave days do I have left this year?",
        )
        print("REPLY:", result.reply)
        print("TRACE:", result.trace)

        # --- Scenario 2: action tool (HITL approval) ---
        print("\n### SCENARIO 2: apply leave (action tool -> approval)")
        result = await run_agent(
            user=user,
            db=db,
            message="Please apply 2 days of sick leave from 2026-07-10 to 2026-07-11, "
            "reason fever.",
        )
        print("REPLY:", result.reply)
        print("PENDING_APPROVAL:", result.pending_approval)
        assert result.pending_approval, "expected an approval request"
        action_id = uuid.UUID(result.pending_approval["action_id"])

        # Simulate the human approving in the Agent Console -> execute the tool.
        action = await db.get(AgentAction, action_id)
        print(f"AgentAction status before: {action.status.value}")
        tool = registry.get(action.tool_name)
        ctx = ToolContext(user=user, db=db)
        exec_result = await tool.handler(ctx, **action.args)
        action.status = ActionStatus.executed
        action.result = exec_result
        await db.commit()
        print("EXECUTED RESULT:", exec_result)

        # Verify a LeaveRequest row now exists.
        rows = (
            await db.execute(
                select(LeaveRequest).where(LeaveRequest.user_id == user.id)
            )
        ).scalars().all()
        print(f"LeaveRequest rows for user: {len(rows)}")
        for r in rows:
            print(f"  - {r.leave_type} {r.start_date}->{r.end_date} ({r.days}d) [{r.status.value}]")


if __name__ == "__main__":
    asyncio.run(main())
