"""Leave-related tools. First real agent capability."""
from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import select

from app.agent.tools import Tool, ToolContext, registry
from app.models.company import Company
from app.models.leave_request import LeaveRequest, LeaveStatus
from app.models.user import User


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


async def _list_my_leaves(ctx: ToolContext) -> dict:
    """The current employee's own leave requests, newest first."""
    rows = (
        await ctx.db.execute(
            select(LeaveRequest)
            .where(LeaveRequest.user_id == ctx.user.id)
            .order_by(LeaveRequest.created_at.desc())
            .limit(50)
        )
    ).scalars().all()
    return {
        "count": len(rows),
        "leaves": [
            {
                "id": str(r.id),
                "type": r.leave_type,
                "from": r.start_date.isoformat(),
                "to": r.end_date.isoformat(),
                "days": r.days,
                "status": r.status.value,
                "reason": r.reason,
            }
            for r in rows
        ],
    }


registry.register(
    Tool(
        name="list_my_leaves",
        description="List the current employee's own leave requests and their statuses.",
        parameters={"type": "object", "properties": {}, "required": []},
        handler=_list_my_leaves,
    )
)


async def _list_pending_leaves(ctx: ToolContext) -> dict:
    """Admin: all pending leave requests in the company, with employee names."""
    rows = (
        await ctx.db.execute(
            select(LeaveRequest, User)
            .join(User, LeaveRequest.user_id == User.id)
            .where(
                LeaveRequest.company_id == ctx.user.company_id,
                LeaveRequest.status == LeaveStatus.pending,
            )
            .order_by(LeaveRequest.created_at.asc())
            .limit(100)
        )
    ).all()
    return {
        "count": len(rows),
        "pending": [
            {
                "id": str(lr.id),
                "employee": u.full_name or u.email,
                "type": lr.leave_type,
                "from": lr.start_date.isoformat(),
                "to": lr.end_date.isoformat(),
                "days": lr.days,
                "reason": lr.reason,
            }
            for lr, u in rows
        ],
    }


registry.register(
    Tool(
        name="list_pending_leaves",
        description="Admin only: list all pending leave requests awaiting approval.",
        parameters={"type": "object", "properties": {}, "required": []},
        handler=_list_pending_leaves,
        admin_only=True,
    )
)


async def _decide_leave(ctx: ToolContext, leave_request_id: str, decision: str) -> dict:
    """Admin: approve or reject a leave request. Approving deducts the days."""
    try:
        lr = await ctx.db.get(LeaveRequest, uuid.UUID(leave_request_id))
    except ValueError:
        return {"error": "invalid leave_request_id"}
    if lr is None or lr.company_id != ctx.user.company_id:
        return {"error": "leave request not found"}
    if lr.status != LeaveStatus.pending:
        return {"error": f"already {lr.status.value}"}

    if decision == "approve":
        lr.status = LeaveStatus.approved
        employee = await ctx.db.get(User, lr.user_id)
        if employee is not None:
            employee.leaves_used += lr.days  # deduct from balance
        await ctx.db.commit()
        return {"id": str(lr.id), "status": "approved", "days_deducted": lr.days}

    lr.status = LeaveStatus.rejected
    await ctx.db.commit()
    return {"id": str(lr.id), "status": "rejected"}


registry.register(
    Tool(
        name="decide_leave",
        description="Admin only: approve or reject a pending leave request by its id. "
        "Approving deducts the days from the employee's balance.",
        parameters={
            "type": "object",
            "properties": {
                "leave_request_id": {"type": "string"},
                "decision": {"type": "string", "enum": ["approve", "reject"]},
            },
            "required": ["leave_request_id", "decision"],
        },
        handler=_decide_leave,
        is_action=True,
        admin_only=True,
        summarize=lambda a: f"{a.get('decision', '?').title()} leave request {a.get('leave_request_id', '')[:8]}",
    )
)
