"""Announcement creation + optional email-blast to the whole company."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations import google_oauth
from app.models.announcement import Announcement
from app.models.google_credential import GoogleCredential
from app.models.user import User


async def create_announcement(
    db: AsyncSession,
    *,
    company_id: uuid.UUID,
    author_id: uuid.UUID,
    title: str,
    body: str,
) -> Announcement:
    ann = Announcement(company_id=company_id, author_id=author_id, title=title, body=body)
    db.add(ann)
    await db.commit()
    await db.refresh(ann)
    return ann


async def email_everyone(
    db: AsyncSession, *, author: User, title: str, body: str
) -> dict:
    """Best-effort email blast to all employees, sent from the author's Gmail."""
    cred = await db.get(GoogleCredential, author.id)
    if cred is None:
        return {"emailed": 0, "note": "Author has not connected Google; skipped emails."}

    recipients = (
        await db.execute(
            select(User.email).where(
                User.company_id == author.company_id, User.id != author.id
            )
        )
    ).scalars().all()
    if not recipients:
        return {"emailed": 0, "note": "No other employees to email."}

    try:
        access = await google_oauth.refresh_access_token(
            google_oauth.decrypt(cred.refresh_token_enc)
        )
    except Exception as exc:  # noqa: BLE001
        return {"emailed": 0, "note": f"Could not get Google token: {exc}"}

    sent = 0
    for email in recipients:
        try:
            await google_oauth.send_gmail(
                access, to=email, subject=f"[Announcement] {title}", body=body
            )
            sent += 1
        except Exception:  # noqa: BLE001 — continue on individual failures
            continue
    return {"emailed": sent, "of": len(recipients)}
