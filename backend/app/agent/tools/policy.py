"""Policy Q&A tool — semantic search over the company's uploaded policies."""
from __future__ import annotations

from sqlalchemy import select

from app.agent.tools import Tool, ToolContext, registry
from app.models.policy import Policy, PolicyChunk
from app.rag.embeddings import embed_query

TOP_K = 4


async def _search_policy(ctx: ToolContext, query: str) -> dict:
    qvec = await embed_query(query)
    rows = (
        await ctx.db.execute(
            select(PolicyChunk.content, Policy.title)
            .join(Policy, PolicyChunk.policy_id == Policy.id)
            .where(PolicyChunk.company_id == ctx.user.company_id)
            .order_by(PolicyChunk.embedding.cosine_distance(qvec))
            .limit(TOP_K)
        )
    ).all()
    if not rows:
        return {"found": False, "note": "No company policies have been uploaded yet."}
    return {
        "found": True,
        "passages": [{"policy": title, "text": content} for content, title in rows],
    }


registry.register(
    Tool(
        name="search_policy",
        description="Search the company's HR policy documents to answer questions about "
        "rules, benefits, leave policy, work-from-home, code of conduct, etc. "
        "Always use this before answering any policy question; quote from the passages.",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The policy question to look up"}
            },
            "required": ["query"],
        },
        handler=_search_policy,
    )
)
