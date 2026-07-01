"""Health + readiness endpoints.

`/health` is intentionally cheap so the GitHub Actions keep-alive cron can ping it
frequently to prevent the free-tier backend/DB from sleeping.
"""
from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from app.agent.groq_pool import groq_pool
from app.db.session import engine

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    """Liveness — always fast, no external calls."""
    return {"status": "ok"}


@router.get("/health/ready")
async def readiness() -> dict:
    """Readiness — checks DB connectivity and Groq key pool status."""
    db_ok = True
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    return {
        "status": "ok" if db_ok else "degraded",
        "database": "up" if db_ok else "down",
        "groq_keys": groq_pool.status(),
    }
