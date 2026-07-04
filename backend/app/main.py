"""FastAPI application entrypoint."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    advisor,
    agent,
    analytics,
    announcements,
    attendance,
    chat,
    company,
    copilot,
    dashboard,
    expenses,
    employees,
    google,
    health,
    hiring,
    leaves,
    me,
    meetings,
    payroll,
    payslips,
    policies,
    tickets,
)
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: start background proactive agents.
    from app.scheduler import start_scheduler, stop_scheduler

    start_scheduler()
    yield
    # Shutdown.
    stop_scheduler()


app = FastAPI(
    title="TalentOS API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow the frontend origin (Vite dev + deployed Vercel URL later).
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(chat.router)
app.include_router(agent.router)
app.include_router(google.router)
app.include_router(employees.router)
app.include_router(me.router)
app.include_router(leaves.router)
app.include_router(policies.router)
app.include_router(announcements.router)
app.include_router(dashboard.router)
app.include_router(payroll.router)
app.include_router(payslips.router)
app.include_router(attendance.router)
app.include_router(analytics.router)
app.include_router(company.router)
app.include_router(tickets.router)
app.include_router(expenses.router)
app.include_router(meetings.router)
app.include_router(copilot.router)
app.include_router(advisor.router)
app.include_router(hiring.router)


@app.get("/")
async def root() -> dict:
    return {"app": "TalentOS", "version": "0.1.0", "docs": "/docs"}
