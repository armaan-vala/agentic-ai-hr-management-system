"""Expense tool — submit a reimbursement claim (action, needs approval)."""
from __future__ import annotations

from app.agent.tools import Tool, ToolContext, registry
from app.models.expense import Expense


async def _submit_expense(
    ctx: ToolContext, amount: int, category: str = "other", description: str | None = ""
) -> dict:
    if amount <= 0:
        return {"error": "amount must be positive"}
    e = Expense(
        company_id=ctx.user.company_id,
        user_id=ctx.user.id,
        amount=amount,
        category=category,
        description=description or "",
    )
    ctx.db.add(e)
    await ctx.db.commit()
    await ctx.db.refresh(e)
    return {"expense_id": str(e.id), "amount": amount, "status": e.status.value}


registry.register(
    Tool(
        name="submit_expense",
        description="Submit an expense / reimbursement claim for the employee. "
        "Amount is a whole number in the company currency. Needs approval before submitting.",
        parameters={
            "type": "object",
            "properties": {
                "amount": {"type": "integer", "description": "Claim amount (whole number)"},
                "category": {
                    "type": "string",
                    "enum": ["travel", "food", "supplies", "other"],
                },
                "description": {"type": ["string", "null"]},
            },
            "required": ["amount"],
        },
        handler=_submit_expense,
        is_action=True,
        summarize=lambda a: f"Submit expense claim of {a.get('amount', '?')} ({a.get('category', 'other')})",
    )
)
