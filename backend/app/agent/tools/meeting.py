"""Meeting tool — schedule a Google Calendar meeting with a Meet link (action, HITL)."""
from __future__ import annotations

from app.agent.tools import Tool, ToolContext, registry
from app.services import calendar as cal


async def _schedule_meeting(
    ctx: ToolContext,
    title: str,
    start: str,
    end: str,
    description: str | None = "",
    attendees: list[str] | None = None,
) -> dict:
    try:
        res = await cal.schedule(
            ctx.db,
            ctx.user,
            title=title,
            description=description or "",
            start_iso=start,
            end_iso=end,
            attendees=attendees or [],
        )
    except cal.NotConnected:
        return {"error": "Google account not connected. Connect it in Settings first."}
    except Exception as exc:  # noqa: BLE001
        return {"error": f"Failed to schedule: {exc}"}
    return {"scheduled": True, "meet_link": res.get("meet_link"), "link": res.get("html_link")}


registry.register(
    Tool(
        name="schedule_meeting",
        description="Schedule a Google Calendar meeting (with a Google Meet link) on the "
        "user's calendar and invite attendees. Times are ISO 8601 local datetimes like "
        "'2026-07-10T15:00:00'. Requires the user to have connected Google. Needs approval.",
        parameters={
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "start": {"type": "string", "description": "ISO datetime, e.g. 2026-07-10T15:00:00"},
                "end": {"type": "string", "description": "ISO datetime"},
                "description": {"type": ["string", "null"]},
                "attendees": {
                    "type": ["array", "null"],
                    "items": {"type": "string"},
                    "description": "Attendee email addresses",
                },
            },
            "required": ["title", "start", "end"],
        },
        handler=_schedule_meeting,
        is_action=True,
        summarize=lambda a: f"Schedule meeting “{a.get('title', '')}” at {a.get('start', '?')}",
    )
)
