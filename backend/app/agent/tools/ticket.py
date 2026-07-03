"""Helpdesk tool — raise a support ticket to HR (action, needs approval)."""
from __future__ import annotations

from app.agent.tools import Tool, ToolContext, registry
from app.models.ticket import Ticket


async def _raise_ticket(ctx: ToolContext, subject: str, message: str) -> dict:
    t = Ticket(
        company_id=ctx.user.company_id,
        user_id=ctx.user.id,
        subject=subject,
        message=message,
    )
    ctx.db.add(t)
    await ctx.db.commit()
    await ctx.db.refresh(t)
    return {"ticket_id": str(t.id), "status": t.status.value, "subject": subject}


registry.register(
    Tool(
        name="raise_ticket",
        description="Raise a helpdesk/support ticket to HR on behalf of the employee "
        "(e.g. a query or issue). This is a real action needing approval.",
        parameters={
            "type": "object",
            "properties": {
                "subject": {"type": "string"},
                "message": {"type": "string"},
            },
            "required": ["subject", "message"],
        },
        handler=_raise_ticket,
        is_action=True,
        summarize=lambda a: f"Raise a ticket: “{a.get('subject', '')}”",
    )
)
