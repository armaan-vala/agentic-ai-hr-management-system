"""
Small helpers for calling the LLM and getting back structured/plain output,
with defensive parsing so a bad LLM response never crashes a request.
"""
from __future__ import annotations

import json
import re

from app.agent.groq_pool import groq_pool
from app.core.config import settings


def llm_available() -> bool:
    return bool(settings.groq_keys)


async def text_completion(system: str, user: str, *, temperature: float = 0.3) -> str:
    """Plain text completion. Returns '' if the LLM is unavailable/fails."""
    if not llm_available():
        return ""
    try:
        resp = await groq_pool.chat(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=temperature,
        )
        return resp["choices"][0]["message"].get("content", "").strip()
    except Exception:
        return ""


def _extract_json(text: str) -> dict | None:
    text = text.strip()
    # strip ```json fences if present
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    try:
        return json.loads(text)
    except Exception:
        # find the first {...} block
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                return None
    return None


async def json_completion(system: str, user: str, *, temperature: float = 0.2) -> dict | None:
    """Ask for JSON and parse it defensively. Returns None if unavailable/unparseable."""
    if not llm_available():
        return None
    text = await text_completion(
        system + " Respond ONLY with valid JSON, no prose, no code fences.",
        user,
        temperature=temperature,
    )
    if not text:
        return None
    return _extract_json(text)
