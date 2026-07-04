"""
Proactive HR Copilot.

run_copilot() runs a set of DETERMINISTIC detectors against the DB (the facts),
then asks the LLM to write a short briefing grounded strictly in those facts.
If the LLM is unavailable it falls back to a template — so it never fails and
never invents numbers.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.groq_pool import groq_pool
from app.core.config import settings
from app.models.attendance import AttendanceRecord
from app.models.company import Company
from app.models.expense import Expense, ExpenseStatus
from app.models.insight import CopilotDigest, Insight
from app.models.leave_request import LeaveRequest, LeaveStatus
from app.models.ticket import Ticket, TicketStatus
from app.models.user import Role, User


async def _count(db: AsyncSession, stmt) -> int:
    return (await db.execute(stmt)).scalar_one() or 0


async def detect(db: AsyncSession, company_id: uuid.UUID) -> list[dict]:
    """Deterministic checks → list of insight dicts. All numbers come from SQL."""
    now = datetime.now(timezone.utc)
    today = now.date()
    insights: list[dict] = []

    # 1. Pending leave approvals
    pending_leaves = await _count(
        db,
        select(func.count(LeaveRequest.id)).where(
            LeaveRequest.company_id == company_id,
            LeaveRequest.status == LeaveStatus.pending,
        ),
    )
    if pending_leaves:
        insights.append({
            "type": "pending_leaves",
            "severity": "warning" if pending_leaves >= 3 else "info",
            "title": f"{pending_leaves} leave request(s) awaiting your approval",
            "detail": "Review and approve/reject in Leave.",
            "action_path": "/leaves",
        })

    # 2. Pending expense claims
    pending_expenses = await _count(
        db,
        select(func.count(Expense.id)).where(
            Expense.company_id == company_id, Expense.status == ExpenseStatus.pending
        ),
    )
    if pending_expenses:
        insights.append({
            "type": "pending_expenses",
            "severity": "warning" if pending_expenses >= 3 else "info",
            "title": f"{pending_expenses} expense claim(s) awaiting approval",
            "detail": "Review reimbursement claims in Expenses.",
            "action_path": "/expenses",
        })

    # 3. Open + aging helpdesk tickets
    open_tickets = await _count(
        db,
        select(func.count(Ticket.id)).where(
            Ticket.company_id == company_id, Ticket.status == TicketStatus.open
        ),
    )
    aging = await _count(
        db,
        select(func.count(Ticket.id)).where(
            Ticket.company_id == company_id,
            Ticket.status == TicketStatus.open,
            Ticket.created_at < now - timedelta(days=3),
        ),
    )
    if open_tickets:
        extra = f" — {aging} open for 3+ days" if aging else ""
        insights.append({
            "type": "open_tickets",
            "severity": "warning" if aging else "info",
            "title": f"{open_tickets} open helpdesk ticket(s){extra}",
            "detail": "Resolve employee queries in Helpdesk.",
            "action_path": "/helpdesk",
        })

    # 4. Employees not clocked in today
    total_emp = await _count(
        db, select(func.count(User.id)).where(User.company_id == company_id)
    )
    clocked_subq = (
        select(AttendanceRecord.user_id).where(
            AttendanceRecord.company_id == company_id,
            AttendanceRecord.date == today,
            AttendanceRecord.clock_in.isnot(None),
        )
    )
    not_clocked = await _count(
        db,
        select(func.count(User.id)).where(
            User.company_id == company_id, User.id.notin_(clocked_subq)
        ),
    )
    # Only surface after mid-day to avoid noise early morning.
    if total_emp and not_clocked and now.hour >= 6:
        insights.append({
            "type": "not_clocked_in",
            "severity": "info",
            "title": f"{not_clocked} of {total_emp} haven't clocked in today",
            "detail": "Check team attendance.",
            "action_path": "/attendance",
        })

    # 5. Low leave balance
    company = await db.get(Company, company_id)
    limit = company.annual_leave_limit if company else 0
    low_balance = await _count(
        db,
        select(func.count(User.id)).where(
            User.company_id == company_id, (limit - User.leaves_used) <= 2
        ),
    )
    if low_balance:
        insights.append({
            "type": "low_balance",
            "severity": "info",
            "title": f"{low_balance} employee(s) have 2 or fewer leave days left",
            "detail": "They may need attention around year-end.",
            "action_path": "/analytics",
        })

    return insights


async def _write_digest(insights: list[dict]) -> tuple[str, bool]:
    """Return (summary, grounded). grounded=False means the LLM fallback was used."""
    if not insights:
        return ("All clear — nothing needs your attention right now. 🎉", True)

    facts = "\n".join(f"- {i['title']}" for i in insights)
    template = "Here's what needs your attention:\n" + facts

    if not settings.groq_keys:
        return (template, False)

    messages = [
        {
            "role": "system",
            "content": (
                "You are an HR operations copilot writing a brief morning briefing for an "
                "HR admin. Use ONLY the facts provided — never invent names, numbers, or "
                "items. Keep it to 2-4 warm, action-oriented sentences."
            ),
        },
        {"role": "user", "content": f"Facts:\n{facts}\n\nWrite the briefing."},
    ]
    try:
        resp = await groq_pool.chat(messages, temperature=0.3)
        text = resp["choices"][0]["message"].get("content", "").strip()
        return (text or template, bool(text))
    except Exception:
        return (template, False)  # reliability: never fail the run


async def run_copilot(db: AsyncSession, company_id: uuid.UUID) -> dict:
    """Run detectors, regenerate insights + digest, persist, and return them."""
    insights = await detect(db, company_id)
    summary, grounded = await _write_digest(insights)

    # Refresh the snapshot (feed reflects current reality).
    await db.execute(delete(Insight).where(Insight.company_id == company_id))
    for i in insights:
        db.add(Insight(company_id=company_id, **i))

    digest = await db.get(CopilotDigest, company_id)
    if digest is None:
        digest = CopilotDigest(company_id=company_id)
        db.add(digest)
    digest.summary = summary
    digest.grounded = grounded
    digest.generated_at = datetime.now(timezone.utc)
    await db.commit()

    return {"summary": summary, "grounded": grounded, "insights": insights}
