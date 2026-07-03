"""Payslip tool — employee asks about their salary/payslip."""
from __future__ import annotations

from sqlalchemy import select

from app.agent.tools import Tool, ToolContext, registry
from app.models.payslip import Payslip, PayslipStatus


async def _get_my_payslip(ctx: ToolContext, month: str = "") -> dict:
    stmt = select(Payslip).where(
        Payslip.user_id == ctx.user.id, Payslip.status == PayslipStatus.released
    )
    if month:
        stmt = stmt.where(Payslip.month == month)
    else:
        stmt = stmt.order_by(Payslip.month.desc())
    p = (await ctx.db.execute(stmt.limit(1))).scalar_one_or_none()
    if p is None:
        return {"found": False, "note": "No released payslip found" + (f" for {month}." if month else ".")}
    return {
        "found": True,
        "month": p.month,
        "currency": p.currency,
        "basic": p.basic,
        "hra": p.hra,
        "allowances": p.allowances,
        "deductions": p.deductions,
        "gross": p.gross,
        "net_take_home": p.net,
    }


registry.register(
    Tool(
        name="get_my_payslip",
        description="Get the current employee's payslip breakdown (net pay, gross, "
        "deductions). Optionally for a specific month 'YYYY-MM'; otherwise the latest.",
        parameters={
            "type": "object",
            "properties": {
                "month": {
                    "type": ["string", "null"],
                    "description": "Optional month as YYYY-MM; omit or null for latest",
                }
            },
            "required": [],
        },
        handler=_get_my_payslip,
    )
)
