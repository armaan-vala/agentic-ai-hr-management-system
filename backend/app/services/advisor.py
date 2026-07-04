"""
Smart Approvals & Triage — AI recommendations grounded in real facts.

Reliability: every recommendation is ADVISORY (the admin still decides). The facts
are pulled deterministically from the DB; the LLM only reasons over them. If the LLM
is unavailable we return a neutral "review" with the facts, so the feature degrades
gracefully instead of failing.
"""
from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.models.expense import Expense
from app.models.leave_request import LeaveRequest, LeaveStatus
from app.models.policy import Policy, PolicyChunk
from app.models.ticket import Ticket
from app.models.user import User
from app.rag.embeddings import embed_query
from app.services.llm_util import json_completion


async def _policy_context(db: AsyncSession, company_id: uuid.UUID, query: str, k: int = 3) -> list[str]:
    """Top policy passages relevant to a query (for grounding)."""
    try:
        qvec = await embed_query(query)
    except Exception:
        return []
    rows = (
        await db.execute(
            select(PolicyChunk.content, Policy.title)
            .join(Policy, PolicyChunk.policy_id == Policy.id)
            .where(PolicyChunk.company_id == company_id)
            .order_by(PolicyChunk.embedding.cosine_distance(qvec))
            .limit(k)
        )
    ).all()
    return [f"[{title}] {content}" for content, title in rows]


# ---------------- Leave ----------------
async def recommend_leave(db: AsyncSession, leave_id: uuid.UUID) -> dict:
    lr = await db.get(LeaveRequest, leave_id)
    if lr is None:
        return {"recommendation": "review", "reason": "Not found", "confidence": "low", "facts": []}
    employee = await db.get(User, lr.user_id)
    company = await db.get(Company, lr.company_id)
    limit = company.annual_leave_limit if company else 0
    balance = limit - (employee.leaves_used if employee else 0)

    taken_this_year = (
        await db.execute(
            select(func.coalesce(func.sum(LeaveRequest.days), 0)).where(
                LeaveRequest.user_id == lr.user_id,
                LeaveRequest.status == LeaveStatus.approved,
            )
        )
    ).scalar_one()

    facts = [
        f"Employee: {employee.full_name or employee.email if employee else 'unknown'}",
        f"Requested: {lr.days} day(s) of {lr.leave_type} leave ({lr.start_date} to {lr.end_date})",
        f"Reason: {lr.reason or 'not given'}",
        f"Current leave balance: {balance} of {limit} days",
        f"Leave already approved this year: {taken_this_year} days",
    ]
    policies = await _policy_context(db, lr.company_id, f"{lr.leave_type} leave policy approval")

    result = await json_completion(
        "You are an HR approval assistant. Given the facts and policy excerpts, recommend "
        "whether to approve this leave. Keys: recommendation ('approve'|'reject'|'review'), "
        "reason (one sentence), confidence ('high'|'medium'|'low').",
        "Facts:\n" + "\n".join(facts) + "\n\nPolicies:\n" + ("\n".join(policies) or "none"),
    )
    if not result:
        # graceful fallback: deterministic hint
        rec = "review" if balance < lr.days else "approve"
        reason = ("Insufficient balance for the requested days." if balance < lr.days
                  else "Balance is sufficient; within normal range.")
        return {"recommendation": rec, "reason": reason, "confidence": "low", "facts": facts}

    return {
        "recommendation": str(result.get("recommendation", "review")).lower(),
        "reason": result.get("reason", ""),
        "confidence": str(result.get("confidence", "medium")).lower(),
        "facts": facts,
    }


# ---------------- Expense ----------------
async def recommend_expense(db: AsyncSession, expense_id: uuid.UUID) -> dict:
    e = await db.get(Expense, expense_id)
    if e is None:
        return {"recommendation": "review", "reason": "Not found", "confidence": "low", "facts": []}
    employee = await db.get(User, e.user_id)
    facts = [
        f"Employee: {employee.full_name or employee.email if employee else 'unknown'}",
        f"Claim: {e.currency} {e.amount} for {e.category}",
        f"Description: {e.description or 'not given'}",
    ]
    policies = await _policy_context(db, e.company_id, f"{e.category} expense reimbursement policy limit")

    result = await json_completion(
        "You are an HR expense-approval assistant. Given the facts and policy excerpts, "
        "recommend approve/reject/review. Keys: recommendation, reason (one sentence), confidence.",
        "Facts:\n" + "\n".join(facts) + "\n\nPolicies:\n" + ("\n".join(policies) or "none"),
    )
    if not result:
        return {"recommendation": "review", "reason": "Manual review recommended.", "confidence": "low", "facts": facts}
    return {
        "recommendation": str(result.get("recommendation", "review")).lower(),
        "reason": result.get("reason", ""),
        "confidence": str(result.get("confidence", "medium")).lower(),
        "facts": facts,
    }


# ---------------- Ticket triage + auto-reply ----------------
async def suggest_ticket_reply(db: AsyncSession, ticket_id: uuid.UUID) -> dict:
    t = await db.get(Ticket, ticket_id)
    if t is None:
        return {"category": "other", "priority": "medium", "draft": "", "grounded": False, "sources": []}
    query = f"{t.subject}. {t.message}"
    policies = await _policy_context(db, t.company_id, query, k=4)

    result = await json_completion(
        "You are an HR helpdesk assistant. Read the employee's ticket and the policy "
        "excerpts. Return keys: category (one of 'IT','HR','Payroll','Leave','Facilities','Other'), "
        "priority ('low'|'medium'|'high'), draft (a helpful reply grounded ONLY in the excerpts; "
        "if the excerpts don't answer it, say it needs a human and keep the draft short), "
        "grounded (true only if your draft is supported by the excerpts).",
        f"Ticket subject: {t.subject}\nTicket message: {t.message}\n\nPolicy excerpts:\n"
        + ("\n".join(policies) or "none"),
    )
    if not result:
        return {"category": "Other", "priority": "medium", "draft": "", "grounded": False,
                "sources": policies}
    return {
        "category": result.get("category", "Other"),
        "priority": str(result.get("priority", "medium")).lower(),
        "draft": result.get("draft", ""),
        "grounded": bool(result.get("grounded", False)),
        "sources": policies,
    }
