"""ATS / hiring — admin-only."""
from __future__ import annotations

import io
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.hiring import Candidate, CandidateStatus, Job, JobStatus
from app.models.user import Role, User
from app.services import hiring as svc

router = APIRouter(prefix="/hiring", tags=["hiring"])


def _admin(user: User) -> None:
    if user.role != Role.admin:
        raise HTTPException(status_code=403, detail="Admin only")


# ---------- Jobs ----------
class JobIn(BaseModel):
    title: str
    department: str = ""
    location: str = ""
    description: str = ""


class JobOut(BaseModel):
    id: str
    title: str
    department: str
    location: str
    description: str
    status: str
    candidate_count: int = 0


class JdBrief(BaseModel):
    title: str
    brief: str
    department: str = ""
    location: str = ""


@router.post("/jobs/generate-jd")
async def generate_jd(body: JdBrief, user: User = Depends(get_current_user)) -> dict:
    _admin(user)
    jd = await svc.generate_jd(body.title, body.brief, department=body.department, location=body.location)
    return {"description": jd or "AI unavailable — write the description manually."}


@router.post("/jobs", response_model=JobOut)
async def create_job(body: JobIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> JobOut:
    _admin(user)
    job = Job(company_id=user.company_id, **body.model_dump())
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return JobOut(id=str(job.id), title=job.title, department=job.department, location=job.location,
                 description=job.description, status=job.status.value)


@router.get("/jobs", response_model=list[JobOut])
async def list_jobs(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> list[JobOut]:
    _admin(user)
    jobs = (await db.execute(select(Job).where(Job.company_id == user.company_id).order_by(Job.created_at.desc()))).scalars().all()
    out = []
    for j in jobs:
        cnt = (await db.execute(select(Candidate).where(Candidate.job_id == j.id))).scalars().all()
        out.append(JobOut(id=str(j.id), title=j.title, department=j.department, location=j.location,
                          description=j.description, status=j.status.value, candidate_count=len(cnt)))
    return out


@router.patch("/jobs/{job_id}", response_model=JobOut)
async def update_job(job_id: uuid.UUID, body: dict, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> JobOut:
    _admin(user)
    job = await db.get(Job, job_id)
    if job is None or job.company_id != user.company_id:
        raise HTTPException(status_code=404, detail="Not found")
    if "status" in body:
        job.status = JobStatus(body["status"])
    for f in ("title", "department", "location", "description"):
        if f in body:
            setattr(job, f, body[f])
    await db.commit()
    await db.refresh(job)
    return JobOut(id=str(job.id), title=job.title, department=job.department, location=job.location,
                 description=job.description, status=job.status.value)


# ---------- Candidates ----------
class CandidateIn(BaseModel):
    name: str
    email: str = ""
    resume_text: str = ""


class CandidateOut(BaseModel):
    id: str
    name: str
    email: str
    score: int | None
    summary: str
    strengths: list[str]
    gaps: list[str]
    status: str


def _cand_out(c: Candidate) -> CandidateOut:
    return CandidateOut(id=str(c.id), name=c.name, email=c.email, score=c.score, summary=c.summary,
                        strengths=c.strengths or [], gaps=c.gaps or [], status=c.status.value)


async def _score_and_save(db: AsyncSession, job: Job, cand: Candidate) -> None:
    result = await svc.score_candidate(job, cand)
    cand.score = result["score"]
    cand.summary = result["summary"]
    cand.strengths = result["strengths"]
    cand.gaps = result["gaps"]
    await db.commit()
    await db.refresh(cand)


@router.post("/jobs/{job_id}/candidates", response_model=CandidateOut)
async def add_candidate(job_id: uuid.UUID, body: CandidateIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> CandidateOut:
    _admin(user)
    job = await db.get(Job, job_id)
    if job is None or job.company_id != user.company_id:
        raise HTTPException(status_code=404, detail="Job not found")
    cand = Candidate(company_id=user.company_id, job_id=job_id, name=body.name, email=body.email, resume_text=body.resume_text)
    db.add(cand)
    await db.commit()
    await db.refresh(cand)
    await _score_and_save(db, job, cand)  # AI score on add
    return _cand_out(cand)


@router.post("/jobs/{job_id}/candidates/upload", response_model=CandidateOut)
async def upload_candidate(job_id: uuid.UUID, name: str = "", file: UploadFile = File(...),
                           user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> CandidateOut:
    _admin(user)
    job = await db.get(Job, job_id)
    if job is None or job.company_id != user.company_id:
        raise HTTPException(status_code=404, detail="Job not found")
    raw = await file.read()
    fname = file.filename or "resume"
    if fname.lower().endswith(".pdf"):
        from pypdf import PdfReader
        text = "\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(raw)).pages)
    else:
        text = raw.decode("utf-8", errors="ignore")
    cand = Candidate(company_id=user.company_id, job_id=job_id,
                     name=name or fname.rsplit(".", 1)[0], resume_text=text)
    db.add(cand)
    await db.commit()
    await db.refresh(cand)
    await _score_and_save(db, job, cand)
    return _cand_out(cand)


@router.get("/jobs/{job_id}/candidates", response_model=list[CandidateOut])
async def list_candidates(job_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> list[CandidateOut]:
    _admin(user)
    rows = (await db.execute(
        select(Candidate).where(Candidate.job_id == job_id, Candidate.company_id == user.company_id)
        .order_by(Candidate.score.desc().nullslast())
    )).scalars().all()
    return [_cand_out(c) for c in rows]


@router.patch("/candidates/{candidate_id}", response_model=CandidateOut)
async def update_candidate(candidate_id: uuid.UUID, body: dict, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> CandidateOut:
    _admin(user)
    c = await db.get(Candidate, candidate_id)
    if c is None or c.company_id != user.company_id:
        raise HTTPException(status_code=404, detail="Not found")
    if "status" in body:
        c.status = CandidateStatus(body["status"])
    await db.commit()
    await db.refresh(c)
    return _cand_out(c)


@router.post("/candidates/{candidate_id}/interview-questions")
async def interview_questions(candidate_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> dict:
    _admin(user)
    c = await db.get(Candidate, candidate_id)
    if c is None or c.company_id != user.company_id:
        raise HTTPException(status_code=404, detail="Not found")
    job = await db.get(Job, c.job_id)
    return {"questions": await svc.interview_questions(job, c)}
