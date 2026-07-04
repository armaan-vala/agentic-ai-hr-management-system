"""
Personalized proactive nudges for each employee (the employee-side copilot).

Deterministic and grounded — every nudge comes from a real DB check, so they are
instant and always accurate.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance import AttendanceRecord
from app.models.company import Company
from app.models.leave_request import LeaveRequest, LeaveStatus
from app.models.payslip import Payslip, PayslipStatus
from app.models.ticket import Ticket, TicketStatus
from app.models.user import Role, User


async def personal_nudges(db: AsyncSession, user: User) -> list[dict]:
    now = datetime.now(timezone.utc)
    today = now.date()
    nudges: list[dict] = []

    # Clock-in reminder (employees)
    if user.role == Role.employee:
        rec = (
            await db.execute(
                select(AttendanceRecord).where(
                    AttendanceRecord.user_id == user.id, AttendanceRecord.date == today
                )
            )
        ).scalar_one_or_none()
        if rec is None or rec.clock_in is None:
            nudges.append({"icon": "🕒", "text": "You haven't clocked in today.", "action_path": "/attendance"})

    # Own pending leave
    pending = (
        await db.execute(
            select(func.count(LeaveRequest.id)).where(
                LeaveRequest.user_id == user.id, LeaveRequest.status == LeaveStatus.pending
            )
        )
    ).scalar_one()
    if pending:
        nudges.append({"icon": "🌴", "text": f"You have {pending} leave request(s) awaiting approval.", "action_path": "/leaves"})

    # Low leave balance
    company = await db.get(Company, user.company_id)
    balance = (company.annual_leave_limit if company else 0) - user.leaves_used
    if balance <= 2:
        nudges.append({"icon": "⚠️", "text": f"Only {balance} leave day(s) left this year.", "action_path": "/leaves"})

    # Latest released payslip
    slip = (
        await db.execute(
            select(Payslip).where(
                Payslip.user_id == user.id, Payslip.status == PayslipStatus.released
            ).order_by(Payslip.month.desc()).limit(1)
        )
    ).scalar_one_or_none()
    if slip:
        nudges.append({"icon": "💰", "text": f"Your payslip for {slip.month} is ready.", "action_path": "/payroll"})

    # Recently resolved ticket
    resolved = (
        await db.execute(
            select(Ticket).where(
                Ticket.user_id == user.id, Ticket.status == TicketStatus.resolved
            ).order_by(Ticket.resolved_at.desc()).limit(1)
        )
    ).scalar_one_or_none()
    if resolved and resolved.admin_response:
        nudges.append({"icon": "🎫", "text": f"HR replied to your ticket: “{resolved.subject}”.", "action_path": "/helpdesk"})

    return nudges
