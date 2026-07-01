"""
Groq multi-key pool.

You provide 2-4 API keys via GROQ_API_KEYS. This pool calls Groq's
OpenAI-compatible chat endpoint, rotating keys round-robin and automatically:
  - putting a key on a short cooldown when it hits a 429 (rate limit),
  - retiring a key that returns 401/403 (invalid),
  - failing over to the next healthy key,
so you never have to swap keys by hand.

In-memory only (no Redis). For a single backend instance this is exactly right.
If you later scale to multiple instances, each keeps its own view — still correct,
just slightly less coordinated on cooldowns.
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field

import httpx

from app.core.config import settings

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
_COOLDOWN_SECONDS = 30.0


@dataclass
class _Key:
    value: str
    cooldown_until: float = 0.0   # epoch seconds; 0 = available now
    dead: bool = False
    calls: int = 0

    def available(self, now: float) -> bool:
        return not self.dead and now >= self.cooldown_until


@dataclass
class GroqPool:
    keys: list[_Key] = field(default_factory=list)
    _idx: int = 0
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    @classmethod
    def from_settings(cls) -> "GroqPool":
        return cls(keys=[_Key(value=k) for k in settings.groq_keys])

    async def _next_key(self) -> _Key | None:
        """Round-robin to the next available key (thread/task-safe)."""
        async with self._lock:
            n = len(self.keys)
            for _ in range(n):
                key = self.keys[self._idx % n]
                self._idx = (self._idx + 1) % n
                if key.available(time.time()):
                    return key
            return None

    async def chat(
        self,
        messages: list[dict],
        *,
        model: str | None = None,
        tools: list[dict] | None = None,
        temperature: float = 0.2,
        max_retries: int = 4,
    ) -> dict:
        """
        Call Groq chat completions with automatic key rotation.
        Returns the raw JSON response dict. Raises RuntimeError if no key works.
        """
        if not self.keys:
            raise RuntimeError("No GROQ_API_KEYS configured.")

        payload: dict = {
            "model": model or settings.groq_model,
            "messages": messages,
            "temperature": temperature,
        }
        if tools:
            payload["tools"] = tools

        last_err: str = "unknown"
        async with httpx.AsyncClient(timeout=60.0) as client:
            for _ in range(max_retries):
                key = await self._next_key()
                if key is None:
                    # All keys cooling down — wait briefly then retry.
                    await asyncio.sleep(2.0)
                    continue

                key.calls += 1
                try:
                    resp = await client.post(
                        GROQ_URL,
                        headers={"Authorization": f"Bearer {key.value}"},
                        json=payload,
                    )
                except httpx.HTTPError as exc:
                    last_err = f"network error: {exc}"
                    continue

                if resp.status_code == 200:
                    return resp.json()
                if resp.status_code == 429:
                    key.cooldown_until = time.time() + _COOLDOWN_SECONDS
                    last_err = "rate limited (429)"
                    continue
                if resp.status_code in (401, 403):
                    key.dead = True
                    last_err = f"invalid key ({resp.status_code})"
                    continue
                # 5xx or other — try another key.
                last_err = f"groq error {resp.status_code}: {resp.text[:200]}"

        raise RuntimeError(f"Groq call failed after {max_retries} tries: {last_err}")

    def status(self) -> list[dict]:
        """Lightweight introspection for a /health or admin view."""
        now = time.time()
        return [
            {
                "index": i,
                "dead": k.dead,
                "cooling_down": now < k.cooldown_until,
                "calls": k.calls,
            }
            for i, k in enumerate(self.keys)
        ]


# Single shared pool for the process.
groq_pool = GroqPool.from_settings()
