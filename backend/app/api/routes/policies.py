"""Policy knowledge base — admin uploads, everyone can read; agent searches via RAG."""
from __future__ import annotations

import io
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.policy import Policy, PolicyChunk
from app.models.user import Role, User
from app.rag.ingest import ingest_policy
from app.rag.samples import SAMPLE_POLICIES

router = APIRouter(prefix="/policies", tags=["policies"])


def _require_admin(user: User) -> None:
    if user.role != Role.admin:
        raise HTTPException(status_code=403, detail="Admin only")


class PolicyIn(BaseModel):
    title: str
    content: str


class PolicyOut(BaseModel):
    id: str
    title: str
    source: str
    chunks: int
    created_at: str


class PolicyDetail(BaseModel):
    id: str
    title: str
    content: str


async def _chunk_count(db: AsyncSession, policy_id: uuid.UUID) -> int:
    return (
        await db.execute(
            select(func.count(PolicyChunk.id)).where(PolicyChunk.policy_id == policy_id)
        )
    ).scalar_one()


@router.get("", response_model=list[PolicyOut])
async def list_policies(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[PolicyOut]:
    rows = (
        await db.execute(
            select(Policy).where(Policy.company_id == user.company_id).order_by(Policy.created_at.desc())
        )
    ).scalars().all()
    out = []
    for p in rows:
        out.append(
            PolicyOut(
                id=str(p.id),
                title=p.title,
                source=p.source,
                chunks=await _chunk_count(db, p.id),
                created_at=p.created_at.isoformat() if p.created_at else "",
            )
        )
    return out


@router.get("/{policy_id}", response_model=PolicyDetail)
async def get_policy(
    policy_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PolicyDetail:
    p = await db.get(Policy, policy_id)
    if p is None or p.company_id != user.company_id:
        raise HTTPException(status_code=404, detail="Not found")
    return PolicyDetail(id=str(p.id), title=p.title, content=p.content)


@router.post("", response_model=PolicyOut)
async def create_policy(
    body: PolicyIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PolicyOut:
    _require_admin(user)
    if not body.content.strip():
        raise HTTPException(status_code=400, detail="Empty content")
    p = await ingest_policy(
        db, company_id=user.company_id, title=body.title or "Untitled", content=body.content
    )
    return PolicyOut(
        id=str(p.id), title=p.title, source=p.source,
        chunks=await _chunk_count(db, p.id),
        created_at=p.created_at.isoformat() if p.created_at else "",
    )


@router.post("/upload", response_model=PolicyOut)
async def upload_policy(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PolicyOut:
    _require_admin(user)
    raw = await file.read()
    name = file.filename or "policy"
    if name.lower().endswith(".pdf"):
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(raw))
        text = "\n".join((page.extract_text() or "") for page in reader.pages)
    else:
        text = raw.decode("utf-8", errors="ignore")
    if not text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text")

    title = name.rsplit(".", 1)[0]
    p = await ingest_policy(
        db, company_id=user.company_id, title=title, content=text, source="file"
    )
    return PolicyOut(
        id=str(p.id), title=p.title, source=p.source,
        chunks=await _chunk_count(db, p.id),
        created_at=p.created_at.isoformat() if p.created_at else "",
    )


@router.post("/seed-samples", response_model=list[PolicyOut])
async def seed_samples(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[PolicyOut]:
    """Load a few starter policies so policy Q&A works out of the box."""
    _require_admin(user)
    out = []
    for sample in SAMPLE_POLICIES:
        p = await ingest_policy(
            db, company_id=user.company_id, title=sample["title"], content=sample["content"]
        )
        out.append(
            PolicyOut(
                id=str(p.id), title=p.title, source=p.source,
                chunks=await _chunk_count(db, p.id),
                created_at=p.created_at.isoformat() if p.created_at else "",
            )
        )
    return out


@router.delete("/{policy_id}")
async def delete_policy(
    policy_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    _require_admin(user)
    p = await db.get(Policy, policy_id)
    if p is None or p.company_id != user.company_id:
        raise HTTPException(status_code=404, detail="Not found")
    await db.delete(p)  # chunks cascade
    await db.commit()
    return {"deleted": True}
