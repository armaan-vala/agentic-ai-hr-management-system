"""
Live test: ingest sample policies, then ask the agent a policy question (RAG).

    docker compose exec -T backend python -m scripts.test_policy
"""
from __future__ import annotations

import asyncio

from sqlalchemy import delete, select

from app.agent.runtime import run_agent
from app.db.session import SessionLocal
from app.models.policy import Policy, PolicyChunk
from app.rag.ingest import ingest_policy
from app.rag.samples import SAMPLE_POLICIES
from scripts.test_agent import TEST_COMPANY_ID, seed


async def main() -> None:
    async with SessionLocal() as db:
        employee, _admin = await seed(db)

        # Clear + re-ingest sample policies for the test company.
        await db.execute(delete(PolicyChunk).where(PolicyChunk.company_id == TEST_COMPANY_ID))
        await db.execute(delete(Policy).where(Policy.company_id == TEST_COMPANY_ID))
        await db.commit()

        print("Ingesting sample policies (first run downloads the embed model)…")
        for s in SAMPLE_POLICIES:
            await ingest_policy(db, company_id=TEST_COMPANY_ID, title=s["title"], content=s["content"])
        total = (
            await db.execute(select(PolicyChunk).where(PolicyChunk.company_id == TEST_COMPANY_ID))
        ).scalars().all()
        print(f"Ingested {len(SAMPLE_POLICIES)} policies, {len(total)} chunks.\n")

        print("### Agent policy Q&A")
        result = await run_agent(
            user=employee,
            db=db,
            message="How many days per week can I work from home, and what are the core hours?",
        )
        print("REPLY:", result.reply)
        print("TOOLS:", [t["tool"] for t in result.trace])


if __name__ == "__main__":
    asyncio.run(main())
