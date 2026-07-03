"""Chunk policy text, embed the chunks, and store them for retrieval."""
from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.policy import Policy, PolicyChunk
from app.rag.embeddings import embed_texts

CHUNK_CHARS = 900      # ~200 tokens
CHUNK_OVERLAP = 150


def chunk_text(text: str) -> list[str]:
    """Split text into overlapping chunks on paragraph-ish boundaries."""
    text = text.strip()
    if not text:
        return []
    chunks: list[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + CHUNK_CHARS, n)
        # try to break on a newline/space near the end for cleaner chunks
        if end < n:
            window = text.rfind("\n", start, end)
            if window == -1:
                window = text.rfind(" ", start, end)
            if window > start + CHUNK_CHARS // 2:
                end = window
        chunks.append(text[start:end].strip())
        start = max(end - CHUNK_OVERLAP, end) if end < n else end
    return [c for c in chunks if c]


async def ingest_policy(
    db: AsyncSession,
    *,
    company_id: uuid.UUID,
    title: str,
    content: str,
    source: str = "text",
) -> Policy:
    policy = Policy(company_id=company_id, title=title, content=content, source=source)
    db.add(policy)
    await db.flush()  # get policy.id

    chunks = chunk_text(content)
    vectors = await embed_texts(chunks)
    for i, (chunk, vec) in enumerate(zip(chunks, vectors)):
        db.add(
            PolicyChunk(
                policy_id=policy.id,
                company_id=company_id,
                chunk_index=i,
                content=chunk,
                embedding=vec,
            )
        )
    await db.commit()
    await db.refresh(policy)
    return policy
