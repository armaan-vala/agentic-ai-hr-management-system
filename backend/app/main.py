"""FastAPI application entrypoint."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    agent,
    announcements,
    attendance,
    chat,
    dashboard,
    employees,
    google,
    health,
    leaves,
    me,
    payroll,
    payslips,
    policies,
)
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: (APScheduler jobs will be started here in a later version.)
    yield
    # Shutdown: place cleanup here.


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


@app.get("/")
async def root() -> dict:
    return {"app": "TalentOS", "version": "0.1.0", "docs": "/docs"}
