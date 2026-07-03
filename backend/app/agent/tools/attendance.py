"""Attendance tools — clock in/out and check today's status."""
from __future__ import annotations

from app.agent.tools import Tool, ToolContext, registry
from app.services import attendance as svc


async def _clock_in(ctx: ToolContext) -> dict:
    return await svc.clock_in(ctx.db, ctx.user)


async def _clock_out(ctx: ToolContext) -> dict:
    return await svc.clock_out(ctx.db, ctx.user)


async def _today(ctx: ToolContext) -> dict:
    return await svc.today_status(ctx.db, ctx.user)


# Clock in/out are low-risk self-service, so they run directly (no approval).
registry.register(
    Tool(
        name="clock_in",
        description="Clock in the current employee for today (mark attendance start).",
        parameters={"type": "object", "properties": {}, "required": []},
        handler=_clock_in,
    )
)
registry.register(
    Tool(
        name="clock_out",
        description="Clock out the current employee for today (mark attendance end).",
        parameters={"type": "object", "properties": {}, "required": []},
        handler=_clock_out,
    )
)
registry.register(
    Tool(
        name="get_attendance_today",
        description="Get the current employee's attendance status for today "
        "(clocked in/out and hours worked).",
        parameters={"type": "object", "properties": {}, "required": []},
        handler=_today,
    )
)
