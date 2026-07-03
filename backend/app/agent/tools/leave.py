"""Leave-related tools. First real agent capability."""
from __future__ import annotations

from datetime import date

from app.agent.tools import Tool, ToolContext, registry
from app.models.company import Company
from app.models.leave_request import LeaveRequest


async def _get_leave_balance(ctx: ToolContext) -> dict:
    """Return the current user's leave balance from real DB data."""
    company = await ctx.db.get(Company, ctx.user.company_id)
    annual_limit = company.annual_leave_limit if company else 0
    used = ctx.user.leaves_used
    return {
        "annual_limit_days": annual_limit,
        "used_days": used,
        "balance_days": annual_limit - used,
    }


registry.register(
    Tool(
        name="get_leave_balance",
        description="Get the current logged-in employee's leave balance "
        "(remaining days, used days, and yearly limit).",
        parameters={"type": "object", "properties": {}, "required": []},
        handler=_get_leave_balance,
        is_action=False,  # read-only, runs without approval
    )
)


async def _apply_leave(
    ctx: ToolContext,
    leave_type: str,
    start_date: str,
    end_date: str,
    reason: str = "",
) -> dict:
    """Create a leave request (inclusive of both dates). Runs only after approval."""
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    if end < start:
        return {"error": "end_date is before start_date"}
    days = (end - start).days + 1

    leave = LeaveRequest(
        company_id=ctx.user.company_id,
        user_id=ctx.user.id,
        leave_type=leave_type,
        start_date=start,
        end_date=end,
        days=days,
        reason=reason,
    )
    ctx.db.add(leave)
    await ctx.db.commit()
    await ctx.db.refresh(leave)
    return {
        "leave_request_id": str(leave.id),
        "days": days,
        "status": leave.status.value,  # 'pending' — awaits HR approval next
    }


registry.register(
    Tool(
        name="apply_leave",
        description="Apply for leave on behalf of the current employee. Dates are "
        "ISO format YYYY-MM-DD and inclusive. This is a real action and requires "
        "the employee's approval before it runs.",
        parameters={
            "type": "object",
            "properties": {
                "leave_type": {
                    "type": "string",
                    "enum": ["casual", "sick", "earned"],
                    "description": "Type of leave",
                },
                "start_date": {"type": "string", "description": "YYYY-MM-DD"},
                "end_date": {"type": "string", "description": "YYYY-MM-DD"},
                "reason": {"type": "string", "description": "Optional reason"},
            },
            "required": ["leave_type", "start_date", "end_date"],
        },
        handler=_apply_leave,
        is_action=True,  # side-effect → human-in-the-loop approval
        summarize=lambda a: (
            f"Apply {a.get('leave_type', '')} leave "
            f"from {a.get('start_date', '?')} to {a.get('end_date', '?')}"
            + (f" (reason: {a['reason']})" if a.get("reason") else "")
        ),
    )
)
