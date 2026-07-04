"""AI Document Studio — generate + understand documents (admin)."""
from __future__ import annotations

import io

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.core.security import get_current_user
from app.models.user import Role, User
from app.services import documents as svc

router = APIRouter(prefix="/documents", tags=["documents"])


def _admin(user: User) -> None:
    if user.role != Role.admin:
        raise HTTPException(status_code=403, detail="Admin only")


class GenerateIn(BaseModel):
    doc_type: str
    details: str


class AnalyzeIn(BaseModel):
    text: str


class QaIn(BaseModel):
    text: str
    question: str


@router.post("/generate")
async def generate(body: GenerateIn, user: User = Depends(get_current_user)) -> dict:
    _admin(user)
    content = await svc.generate_document(body.doc_type, body.details)
    return {"content": content or "AI unavailable — please write manually."}


@router.post("/analyze")
async def analyze(body: AnalyzeIn, user: User = Depends(get_current_user)) -> dict:
    _admin(user)
    if not body.text.strip():
        raise HTTPException(status_code=400, detail="Empty text")
    return await svc.analyze_document(body.text)


@router.post("/analyze-upload")
async def analyze_upload(file: UploadFile = File(...), user: User = Depends(get_current_user)) -> dict:
    _admin(user)
    raw = await file.read()
    name = file.filename or "doc"
    if name.lower().endswith(".pdf"):
        from pypdf import PdfReader

        text = "\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(raw)).pages)
    else:
        text = raw.decode("utf-8", errors="ignore")
    if not text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text")
    result = await svc.analyze_document(text)
    result["text"] = text  # return extracted text so the UI can run Q&A on it
    return result


@router.post("/qa")
async def qa(body: QaIn, user: User = Depends(get_current_user)) -> dict:
    _admin(user)
    return {"answer": await svc.answer_about(body.text, body.question)}
