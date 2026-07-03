"""Live test: admin agent posts an announcement (HITL)."""
from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.agent.runtime import run_agent
from app.agent.tools import ToolContext, registry
from app.db.session import SessionLocal
from app.models.announcement import Announcement
from scripts.test_agent import seed


async def main() -> None:
    async with SessionLocal() as db:
        _employee, admin = await seed(db)

        result = await run_agent(
            user=admin,
            db=db,
            message="Post an announcement titled 'Diwali Holiday' saying the office is "
            "closed next Monday for Diwali.",
        )
        print("REPLY:", result.reply)
        print("PENDING:", result.pending_approval)
        assert result.pending_approval, "expected approval for post_announcement"

        tool = registry.get(result.pending_approval["tool"])
        ctx = ToolContext(user=admin, db=db)
        res = await tool.handler(ctx, **result.pending_approval["args"])
        print("EXECUTED:", res)

        rows = (
            await db.execute(
                select(Announcement).where(Announcement.company_id == admin.company_id)
            )
        ).scalars().all()
        print(f"Announcements in company: {len(rows)}")
        for a in rows[:3]:
            print(f"  - {a.title}")


if __name__ == "__main__":
    asyncio.run(main())
