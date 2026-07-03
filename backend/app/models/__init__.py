"""Import all models here so Alembic autogenerate can discover them."""
from app.models.agent_action import AgentAction
from app.models.company import Company
from app.models.google_credential import GoogleCredential
from app.models.leave_request import LeaveRequest
from app.models.user import User

__all__ = ["AgentAction", "Company", "GoogleCredential", "LeaveRequest", "User"]
