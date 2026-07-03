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
TEST_ADMIN_ID = uuid.uuid5(uuid.NAMESPACE_DNS, "talentos-test-admin")


async def _upsert(db, model, pk, **fields):
    obj = await db.get(model, pk)
    if obj is None:
        obj = model(id=pk, **fields)
        db.add(obj)
    else:
        for k, v in fields.items():
            setattr(obj, k, v)
    return obj


async def seed(db) -> tuple[User, User]:
    await _upsert(db, Company, TEST_COMPANY_ID, name="Test Co", annual_leave_limit=12)
    await db.flush()

    employee = await _upsert(
        db, User, TEST_USER_ID,
        company_id=TEST_COMPANY_ID, email="rahul@testco.com",
        full_name="Rahul", role=Role.employee, leaves_used=3,
    )
    admin = await _upsert(
        db, User, TEST_ADMIN_ID,
        company_id=TEST_COMPANY_ID, email="hr@testco.com",
        full_name="HR Admin", role=Role.admin, leaves_used=0,
    )

    # Clean prior test leave requests for deterministic runs.
    old = (
        await db.execute(select(LeaveRequest).where(LeaveRequest.user_id == TEST_USER_ID))
    ).scalars().all()
    for lr in old:
        await db.delete(lr)

    await db.commit()
    await db.refresh(employee)
    await db.refresh(admin)
    return employee, admin


async def main() -> None:
    async with SessionLocal() as db:
        user, admin = await seed(db)
        print(f"Employee: {user.full_name} used={user.leaves_used} | Admin: {admin.full_name}\n")

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
        pending_leave_id = rows[0].id

        # --- Scenario 3: admin sees pending + approves (role-gated tools) ---
        print("\n### SCENARIO 3: admin lists pending leaves (admin-only tool)")
        result = await run_agent(
            user=admin, db=db, message="Show me all pending leave requests."
        )
        print("REPLY:", result.reply)
        print("TRACE tools:", [t["tool"] for t in result.trace])

        # role filtering: employee must NOT see admin tools
        emp_tools = {t["function"]["name"] for t in registry.schemas(include_admin=False)}
        adm_tools = {t["function"]["name"] for t in registry.schemas(include_admin=True)}
        print("employee sees decide_leave? ", "decide_leave" in emp_tools, "(should be False)")
        print("admin sees decide_leave?    ", "decide_leave" in adm_tools, "(should be True)")

        # approve the pending leave directly (tool logic) and check balance change
        print("\n### approve pending leave -> balance should drop")
        before = (await db.get(User, TEST_USER_ID)).leaves_used
        ctx_admin = ToolContext(user=admin, db=db)
        decide = registry.get("decide_leave")
        dres = await decide.handler(
            ctx_admin, leave_request_id=str(pending_leave_id), decision="approve"
        )
        after = (await db.get(User, TEST_USER_ID)).leaves_used
        print("decide result:", dres)
        print(f"leaves_used: {before} -> {after} (expected +2)")


if __name__ == "__main__":
    asyncio.run(main())
