"""Email tool — sends from the current user's connected Gmail (action, needs approval)."""
from __future__ import annotations

from app.agent.tools import Tool, ToolContext, registry
from app.integrations import google_oauth
from app.models.google_credential import GoogleCredential


async def _send_email(
    ctx: ToolContext, to: str, subject: str, body: str
) -> dict:
    cred = await ctx.db.get(GoogleCredential, ctx.user.id)
    if cred is None:
        return {
            "error": "Google account not connected. "
            "Connect Gmail in Settings first, then try again."
        }
    try:
        refresh_token = google_oauth.decrypt(cred.refresh_token_enc)
        access_token = await google_oauth.refresh_access_token(refresh_token)
        sent = await google_oauth.send_gmail(
            access_token, to=to, subject=subject, body=body
        )
    except Exception as exc:  # noqa: BLE001 — surface failure to the console
        return {"error": f"Failed to send: {exc}"}
    return {"sent": True, "to": to, "gmail_message_id": sent.get("id"), "from": cred.google_email}


registry.register(
    Tool(
        name="send_email",
        description="Send an email from the current user's connected Gmail account. "
        "Requires the user to have connected Google. This is a real action and "
        "needs approval before sending.",
        parameters={
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Recipient email address"},
                "subject": {"type": "string"},
                "body": {"type": "string", "description": "Plain-text email body"},
            },
            "required": ["to", "subject", "body"],
        },
        handler=_send_email,
        is_action=True,
        summarize=lambda a: f"Send email to {a.get('to', '?')} — “{a.get('subject', '')}”",
    )
)
