"""Import all models here so Alembic autogenerate can discover them."""
from app.models.agent_action import AgentAction
from app.models.announcement import Announcement
from app.models.attendance import AttendanceRecord
from app.models.company import Company
from app.models.expense import Expense
from app.models.google_credential import GoogleCredential
from app.models.insight import CopilotDigest, Insight
from app.models.leave_request import LeaveRequest
from app.models.payslip import Payslip
from app.models.policy import Policy, PolicyChunk
from app.models.salary_structure import SalaryStructure
from app.models.ticket import Ticket
from app.models.user import User

__all__ = [
    "AgentAction",
    "Announcement",
    "AttendanceRecord",
    "Company",
    "CopilotDigest",
    "Expense",
    "GoogleCredential",
    "Insight",
    "LeaveRequest",
    "Payslip",
    "Policy",
    "PolicyChunk",
    "SalaryStructure",
    "Ticket",
    "User",
]
