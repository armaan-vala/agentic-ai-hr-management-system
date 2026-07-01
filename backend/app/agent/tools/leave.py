"""Leave-related tools. First real agent capability."""
from __future__ import annotations

from app.agent.tools import Tool, ToolContext, registry
from app.models.company import Company


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
