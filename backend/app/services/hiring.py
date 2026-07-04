"""
AI hiring — JD generation, resume scoring, interview questions.

Reliability: scoring is grounded in the actual resume text + job description that
were provided (no external claims). Structured JSON is parsed defensively; if the
LLM is unavailable, the candidate is stored unscored rather than failing.
"""
from __future__ import annotations

from app.models.hiring import Candidate, Job
from app.services.llm_util import json_completion, text_completion


async def generate_jd(title: str, brief: str, *, department: str = "", location: str = "") -> str:
    """Draft a full job description from a short brief."""
    ctx = f"Title: {title}\nDepartment: {department}\nLocation: {location}\nBrief: {brief}"
    jd = await text_completion(
        "You are an expert technical recruiter. Write a clear, structured job description "
        "with sections: About the Role, Responsibilities, Requirements, Nice to have. "
        "Keep it concise and professional. Plain text with simple headings.",
        ctx,
        temperature=0.5,
    )
    return jd


async def score_candidate(job: Job, candidate: Candidate) -> dict:
    """Score a resume against the job. Returns {score, summary, strengths, gaps}."""
    if not candidate.resume_text.strip():
        return {"score": None, "summary": "No resume text provided.", "strengths": [], "gaps": []}

    result = await json_completion(
        "You are a hiring assistant screening a candidate against a job. Judge ONLY from the "
        "resume and job description provided; do not assume facts not present. Return keys: "
        "score (integer 0-100 match), summary (2-3 sentences), strengths (array of short strings), "
        "gaps (array of short strings).",
        f"JOB DESCRIPTION:\n{job.title}\n{job.description}\n\nRESUME:\n{candidate.resume_text[:6000]}",
    )
    if not result:
        return {"score": None, "summary": "AI scoring unavailable — review manually.", "strengths": [], "gaps": []}

    try:
        score = int(result.get("score"))
        score = max(0, min(100, score))
    except (TypeError, ValueError):
        score = None
    return {
        "score": score,
        "summary": str(result.get("summary", ""))[:1500],
        "strengths": [str(s) for s in (result.get("strengths") or [])][:8],
        "gaps": [str(g) for g in (result.get("gaps") or [])][:8],
    }


async def interview_questions(job: Job, candidate: Candidate) -> list[str]:
    """Tailored interview questions for this candidate + role."""
    result = await json_completion(
        "You are an interviewer. Generate 6 targeted interview questions for this candidate "
        "based on the job and their resume (mix of role-fit, depth on their experience, and "
        "gaps to probe). Return JSON: {questions: [array of strings]}.",
        f"JOB:\n{job.title}\n{job.description[:1500]}\n\nRESUME:\n{candidate.resume_text[:4000]}",
    )
    if result and isinstance(result.get("questions"), list):
        return [str(q) for q in result["questions"]][:10]
    return []
