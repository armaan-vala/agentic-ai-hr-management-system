"""Async SQLAlchemy engine + session factory + declarative base."""
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    """Base class for all ORM models."""


# `echo` on in dev to see SQL; off in prod. pool_pre_ping avoids stale connections
# (important on Supabase's pooler which can drop idle connections).
engine = create_async_engine(
    settings.database_url,
    echo=not settings.is_prod,
    pool_pre_ping=True,
)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a DB session and always closes it."""
    async with SessionLocal() as session:
        yield session
