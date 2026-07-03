"""Announcement tool — admin posts a company-wide announcement (action, needs approval)."""
from __future__ import annotations

from app.agent.tools import Tool, ToolContext, registry
from app.services import announcements as svc


async def _post_announcement(
    ctx: ToolContext, title: str, body: str, email_everyone: bool = False
) -> dict:
    ann = await svc.create_announcement(
        ctx.db,
        company_id=ctx.user.company_id,
        author_id=ctx.user.id,
        title=title,
        body=body,
    )
    result = {"announcement_id": str(ann.id), "posted": True}
    if email_everyone:
        result["email"] = await svc.email_everyone(
            ctx.db, author=ctx.user, title=title, body=body
        )
    return result


registry.register(
    Tool(
        name="post_announcement",
        description="Admin only: post a company-wide announcement to the feed, and "
        "optionally email it to all employees. This is a real action needing approval.",
        parameters={
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "body": {"type": "string"},
                "email_everyone": {
                    "type": "boolean",
                    "description": "Also email all employees (from your connected Gmail)",
                },
            },
            "required": ["title", "body"],
        },
        handler=_post_announcement,
        is_action=True,
        admin_only=True,
        summarize=lambda a: (
            f"Post announcement “{a.get('title', '')}”"
            + (" and email everyone" if a.get("email_everyone") else "")
        ),
    )
)
