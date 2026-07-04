"""
Background scheduler for proactive agents (no Redis — APScheduler in-process).

Runs the HR Copilot for every company on a daily schedule. Each company is
isolated so one failure never blocks the others.
"""
from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.company import Company
from app.services import copilot

logger = logging.getLogger("talentos.scheduler")

scheduler = AsyncIOScheduler(timezone="UTC")


async def run_copilot_for_all() -> None:
    async with SessionLocal() as db:
        company_ids = (await db.execute(select(Company.id))).scalars().all()
        for cid in company_ids:
            try:
                await copilot.run_copilot(db, cid)
            except Exception:  # noqa: BLE001 — isolate per-company failures
                logger.exception("Copilot run failed for company %s", cid)


def start_scheduler() -> None:
    # Daily briefing at 06:00 UTC. (Manual /copilot/run is available anytime.)
    scheduler.add_job(
        run_copilot_for_all,
        trigger="cron",
        hour=6,
        minute=0,
        id="daily_copilot",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    scheduler.start()
    logger.info("Scheduler started (daily copilot at 06:00 UTC)")


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
