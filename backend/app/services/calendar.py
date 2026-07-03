"""Calendar meeting scheduling on top of the user's connected Google account."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations import google_oauth
from app.models.google_credential import GoogleCredential
from app.models.user import User


class NotConnected(Exception):
    pass


async def _access_token(db: AsyncSession, user: User) -> str:
    cred = await db.get(GoogleCredential, user.id)
    if cred is None:
        raise NotConnected("Google account not connected.")
    refresh = google_oauth.decrypt(cred.refresh_token_enc)
    return await google_oauth.refresh_access_token(refresh)


async def schedule(
    db: AsyncSession,
    user: User,
    *,
    title: str,
    description: str,
    start_iso: str,
    end_iso: str,
    attendees: list[str] | None = None,
) -> dict:
    token = await _access_token(db, user)
    return await google_oauth.create_calendar_event(
        token,
        summary=title,
        description=description,
        start_iso=start_iso,
        end_iso=end_iso,
        attendees=attendees,
    )


async def upcoming(db: AsyncSession, user: User) -> list[dict]:
    token = await _access_token(db, user)
    now_iso = datetime.now(timezone.utc).isoformat()
    return await google_oauth.list_calendar_events(token, time_min_iso=now_iso)
