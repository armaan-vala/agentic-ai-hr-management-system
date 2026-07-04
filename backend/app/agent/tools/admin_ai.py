"""
Agent tools that expose the AI-first admin features to the chat assistant.

All admin-only. Reads return real data; create_job is a side-effecting action (HITL).
"""
from __future__ import annotations

from sqlalchemy import func, select

from app.agent.tools import Tool, ToolContext, registry
from app.models.hiring import Candidate, Job, JobStatus
from app.services import analytics_ai, documents, hiring
from app.services.copilot import detect


# ---------- Analytics ----------
async def _workforce_metrics(ctx: ToolContext) -> dict:
    return await analytics_ai.build_snapshot(ctx.db, ctx.user.company_id)


registry.register(Tool(
    name="get_workforce_metrics",
    description="Admin only: get a snapshot of company workforce metrics (headcount, "
    "attendance, leave, expenses, tickets, hiring funnel). Use this to answer any "
    "analytics/reporting question with real numbers.",
    parameters={"type": "object", "properties": {}, "required": []},
    handler=_workforce_metrics,
    admin_only=True,
))


# ---------- Copilot insights ----------
async def _hr_insights(ctx: ToolContext) -> dict:
    return {"insights": await detect(ctx.db, ctx.user.company_id)}


registry.register(Tool(
    name="get_hr_insights",
    description="Admin only: get the current proactive HR insights (pending approvals, "
    "aging tickets, who hasn't clocked in, low leave balances).",
    parameters={"type": "object", "properties": {}, "required": []},
    handler=_hr_insights,
    admin_only=True,
))


# ---------- Hiring ----------
async def _list_jobs(ctx: ToolContext) -> dict:
    rows = (await ctx.db.execute(
        select(Job).where(Job.company_id == ctx.user.company_id).order_by(Job.created_at.desc())
    )).scalars().all()
    out = []
    for j in rows:
        cnt = (await ctx.db.execute(
            select(func.count(Candidate.id)).where(Candidate.job_id == j.id)
        )).scalar_one()
        out.append({"id": str(j.id), "title": j.title, "status": j.status.value, "candidates": cnt})
    return {"jobs": out}


registry.register(Tool(
    name="list_jobs",
    description="Admin only: list open/closed job postings with candidate counts.",
    parameters={"type": "object", "properties": {}, "required": []},
    handler=_list_jobs,
    admin_only=True,
))


async def _top_candidates(ctx: ToolContext, job_title=None, limit=5) -> dict:
    limit = limit or 5
    q = select(Job).where(Job.company_id == ctx.user.company_id)
    if job_title:
        q = q.where(Job.title.ilike(f"%{job_title}%"))
    job = (await ctx.db.execute(q.order_by(Job.created_at.desc()).limit(1))).scalar_one_or_none()
    if job is None:
        return {"found": False, "note": "No matching job found."}
    rows = (await ctx.db.execute(
        select(Candidate).where(Candidate.job_id == job.id)
        .order_by(Candidate.score.desc().nullslast()).limit(min(limit, 10))
    )).scalars().all()
    return {
        "job": job.title,
        "candidates": [
            {"name": c.name, "score": c.score, "status": c.status.value, "summary": c.summary}
            for c in rows
        ],
    }


registry.register(Tool(
    name="list_top_candidates",
    description="Admin only: list the top AI-scored candidates for a job (by match score). "
    "Optionally filter by job title.",
    parameters={
        "type": "object",
        "properties": {
            "job_title": {"type": ["string", "null"], "description": "Job title to match"},
            "limit": {"type": ["integer", "null"]},
        },
        "required": [],
    },
    handler=_top_candidates,
    admin_only=True,
))


async def _create_job(ctx: ToolContext, title: str, brief=None, department=None, location=None) -> dict:
    brief, department, location = brief or "", department or "", location or ""
    jd = await hiring.generate_jd(title, brief, department=department, location=location)
    job = Job(company_id=ctx.user.company_id, title=title, department=department, location=location, description=jd)
    ctx.db.add(job)
    await ctx.db.commit()
    await ctx.db.refresh(job)
    return {"job_id": str(job.id), "title": title, "status": job.status.value}


registry.register(Tool(
    name="create_job",
    description="Admin only: create a new job posting. Generates a job description from the "
    "brief automatically. This is a real action and needs approval.",
    parameters={
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "brief": {"type": ["string", "null"], "description": "Key requirements to draft the JD"},
            "department": {"type": ["string", "null"]},
            "location": {"type": ["string", "null"]},
        },
        "required": ["title"],
    },
    handler=_create_job,
    is_action=True,
    admin_only=True,
    summarize=lambda a: f"Create job posting: {a.get('title', '')}",
))


# ---------- Document generation ----------
async def _generate_document(ctx: ToolContext, doc_type: str, details: str) -> dict:
    content = await documents.generate_document(doc_type, details)
    return {"content": content or "AI unavailable."}


registry.register(Tool(
    name="generate_document",
    description="Admin only: draft an HR document. doc_type is one of offer_letter, policy, "
    "email, warning_letter, job_description, custom. 'details' describes what's needed.",
    parameters={
        "type": "object",
        "properties": {
            "doc_type": {
                "type": "string",
                "enum": ["offer_letter", "policy", "email", "warning_letter", "job_description", "custom"],
            },
            "details": {"type": "string"},
        },
        "required": ["doc_type", "details"],
    },
    handler=_generate_document,
    admin_only=True,
))
