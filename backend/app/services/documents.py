"""
AI Document Studio — generate and understand HR documents.

Generation is clearly AI-authored (admin reviews before use). Understanding is
grounded strictly in the uploaded text. Both degrade gracefully if the LLM is down.
"""
from __future__ import annotations

from app.services.llm_util import json_completion, text_completion

DOC_PROMPTS = {
    "offer_letter": "Write a warm, professional job offer letter. Include role, compensation, "
    "start date, and a friendly closing. Use placeholders like [Company] only if a detail is missing.",
    "policy": "Write a clear, well-structured HR policy document with numbered sections.",
    "email": "Write a concise, professional HR email.",
    "warning_letter": "Write a firm but respectful formal warning letter, factual and compliant in tone.",
    "job_description": "Write a structured job description (About, Responsibilities, Requirements, Nice to have).",
    "custom": "Write the requested HR document in a clear, professional tone.",
}


async def generate_document(doc_type: str, details: str) -> str:
    guide = DOC_PROMPTS.get(doc_type, DOC_PROMPTS["custom"])
    return await text_completion(
        f"You are an expert HR writer. {guide} Output only the document text.",
        details,
        temperature=0.5,
    )


async def analyze_document(text: str) -> dict:
    result = await json_completion(
        "You are an HR/legal assistant. Analyze the document. Return keys: summary "
        "(2-3 sentences), key_terms (array of short strings for important clauses/terms), "
        "red_flags (array of short strings for anything unusual, risky, or missing; empty "
        "if none). Base everything ONLY on the document text.",
        text[:8000],
    )
    if not result:
        return {"summary": "AI unavailable — please review the document manually.",
                "key_terms": [], "red_flags": []}
    return {
        "summary": str(result.get("summary", "")),
        "key_terms": [str(t) for t in (result.get("key_terms") or [])][:12],
        "red_flags": [str(f) for f in (result.get("red_flags") or [])][:12],
    }


async def answer_about(text: str, question: str) -> str:
    ans = await text_completion(
        "Answer the question using ONLY the document text provided. If the document does "
        "not contain the answer, say so. Quote the relevant part when helpful.",
        f"DOCUMENT:\n{text[:8000]}\n\nQUESTION: {question}",
    )
    return ans or "AI is unavailable right now."
