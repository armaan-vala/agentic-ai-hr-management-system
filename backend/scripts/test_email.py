"""
Live test: agent sends a real email from the connected Gmail (HITL approved).

Run inside the container AFTER connecting Google for the test user:
    docker compose exec -T backend python -m scripts.test_email
"""
from __future__ import annotations

import asyncio
import uuid

from app.agent.runtime import run_agent
from app.agent.tools import ToolContext, registry
from app.db.session import SessionLocal
from app.models.google_credential import GoogleCredential
from app.models.user import User

TEST_USER_ID = uuid.uuid5(uuid.NAMESPACE_DNS, "talentos-test-user")


async def main() -> None:
    async with SessionLocal() as db:
        user = await db.get(User, TEST_USER_ID)
        cred = await db.get(GoogleCredential, TEST_USER_ID)
        if cred is None:
            print("No Google credential for test user — connect first.")
            return
        to_addr = cred.google_email
        print(f"Connected Gmail: {to_addr}\n")

        # Ask the agent to send an email (to the connected address itself).
        print("### Agent: send email")
        result = await run_agent(
            user=user,
            db=db,
            message=(
                f"Send an email to {to_addr} with the subject "
                f"'TalentOS agent test' and body "
                f"'Hello! This email was sent by my agentic HRMS assistant. It works.'"
            ),
        )
        print("REPLY:", result.reply)
        print("PENDING_APPROVAL:", result.pending_approval)
        assert result.pending_approval, "expected approval request for send_email"

        # Simulate the human approving -> execute the send_email tool for real.
        print("\n### Approved -> sending for real")
        tool = registry.get(result.pending_approval["tool"])
        ctx = ToolContext(user=user, db=db)
        exec_result = await tool.handler(ctx, **result.pending_approval["args"])
        print("SEND RESULT:", exec_result)


if __name__ == "__main__":
    asyncio.run(main())
