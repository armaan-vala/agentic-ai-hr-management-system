"""
Natural-language analytics.

Reliability: we do NOT let the LLM write SQL. We compute a deterministic metrics
snapshot, then let the LLM answer the admin's question grounded strictly in those
numbers. So answers can never contain invented figures.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance import AttendanceRecord
from app.models.company import Company
from app.models.expense import Expense, ExpenseStatus
from app.models.hiring import Candidate, CandidateStatus, Job, JobStatus
from app.models.leave_request import LeaveRequest, LeaveStatus
from app.models.ticket import Ticket, TicketStatus
from app.models.user import Role, User
from app.services.llm_util import text_completion


async def _scalar(db: AsyncSession, stmt) -> int:
    return (await db.execute(stmt)).scalar_one() or 0


async def build_snapshot(db: AsyncSession, company_id: uuid.UUID) -> dict:
    today = datetime.now(timezone.utc).date()
    cid = company_id

    async def cnt(model, *conds):
        return await _scalar(db, select(func.count(model.id)).where(model.company_id == cid, *conds))

    company = await db.get(Company, cid)
    headcount = await cnt(User)
    admins = await _scalar(db, select(func.count(User.id)).where(User.company_id == cid, User.role == Role.admin))

    present_today = await _scalar(db, select(func.count(AttendanceRecord.id)).where(
        AttendanceRecord.company_id == cid, AttendanceRecord.date == today, AttendanceRecord.clock_in.isnot(None)))

    leave_days_taken = await _scalar(db, select(func.coalesce(func.sum(LeaveRequest.days), 0)).where(
        LeaveRequest.company_id == cid, LeaveRequest.status == LeaveStatus.approved))

    exp_pending_amt = await _scalar(db, select(func.coalesce(func.sum(Expense.amount), 0)).where(
        Expense.company_id == cid, Expense.status == ExpenseStatus.pending))

    return {
        "company": company.name if company else "",
        "annual_leave_limit": company.annual_leave_limit if company else 0,
        "headcount": headcount,
        "admins": admins,
        "employees": headcount - admins,
        "present_today": present_today,
        "absent_today": headcount - present_today,
        "leaves_pending": await cnt(LeaveRequest, LeaveRequest.status == LeaveStatus.pending),
        "leaves_approved": await cnt(LeaveRequest, LeaveRequest.status == LeaveStatus.approved),
        "leaves_rejected": await cnt(LeaveRequest, LeaveRequest.status == LeaveStatus.rejected),
        "total_leave_days_taken": leave_days_taken,
        "expenses_pending": await cnt(Expense, Expense.status == ExpenseStatus.pending),
        "expenses_pending_amount": exp_pending_amt,
        "tickets_open": await cnt(Ticket, Ticket.status == TicketStatus.open),
        "tickets_resolved": await cnt(Ticket, Ticket.status == TicketStatus.resolved),
        "open_jobs": await cnt(Job, Job.status == JobStatus.open),
        "total_candidates": await cnt(Candidate),
        "shortlisted_candidates": await cnt(Candidate, Candidate.status == CandidateStatus.shortlisted),
    }


def _snapshot_text(s: dict) -> str:
    return "\n".join(f"{k}: {v}" for k, v in s.items())


async def ask(db: AsyncSession, company_id: uuid.UUID, question: str) -> dict:
    snapshot = await build_snapshot(db, company_id)
    facts = _snapshot_text(snapshot)

    answer = await text_completion(
        "You are a people-analytics assistant for an HR admin. Answer the question using "
        "ONLY the metrics provided. Cite the specific numbers you used. If the metrics do "
        "not contain the answer, say so plainly. Be concise (2-4 sentences).",
        f"Metrics:\n{facts}\n\nQuestion: {question}",
    )
    if not answer:
        answer = "AI is unavailable right now. Here are the raw metrics:\n" + facts
    return {"answer": answer, "metrics": snapshot}
