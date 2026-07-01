"""Import all models here so Alembic autogenerate can discover them."""
from app.models.company import Company
from app.models.user import User

__all__ = ["Company", "User"]
