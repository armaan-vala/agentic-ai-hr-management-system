"""Google account connect flow (per-user OAuth for Gmail send)."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import get_current_user
from app.db.session import get_db
from app.integrations import google_oauth
from app.models.google_credential import GoogleCredential
from app.models.user import User

router = APIRouter(prefix="/google", tags=["google"])

_STATE_ALG = "HS256"


class ConnectOut(BaseModel):
    auth_url: str


class StatusOut(BaseModel):
    connected: bool
    email: str = ""


@router.get("/connect", response_model=ConnectOut)
async def connect(user: User = Depends(get_current_user)) -> ConnectOut:
    """Return the Google consent URL. Frontend redirects the browser to it."""
    if not settings.google_client_id:
        raise HTTPException(status_code=503, detail="Google OAuth not configured")
    state = jwt.encode(
        {
            "sub": str(user.id),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=10),
        },
        settings.app_secret,
        algorithm=_STATE_ALG,
    )
    return ConnectOut(auth_url=google_oauth.build_auth_url(state))


@router.get("/callback")
async def callback(
    state: str = Query(...),
    code: str | None = Query(default=None),
    error: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """Google redirects here after consent. No auth header — identity is in `state`."""
    if error or not code:
        return RedirectResponse(url=f"{settings.google_post_connect_redirect}&error=1")
    try:
        payload = jwt.decode(state, settings.app_secret, algorithms=[_STATE_ALG])
        user_id = uuid.UUID(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid state")

    tokens = await google_oauth.exchange_code(code)
    if not tokens["refresh_token"]:
        # Google withholds the refresh token if already granted; prompt=consent avoids this.
        return RedirectResponse(url=f"{settings.google_post_connect_redirect}&error=norefresh")

    cred = await db.get(GoogleCredential, user_id)
    if cred is None:
        cred = GoogleCredential(user_id=user_id)
        db.add(cred)
    cred.google_email = tokens["email"]
    cred.refresh_token_enc = google_oauth.encrypt(tokens["refresh_token"])
    cred.scopes = " ".join(google_oauth.SCOPES)
    await db.commit()

    return RedirectResponse(url=settings.google_post_connect_redirect)


@router.get("/status", response_model=StatusOut)
async def status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StatusOut:
    cred = await db.get(GoogleCredential, user.id)
    if cred is None:
        return StatusOut(connected=False)
    return StatusOut(connected=True, email=cred.google_email)


@router.delete("/disconnect")
async def disconnect(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    cred = await db.get(GoogleCredential, user.id)
    if cred is not None:
        await db.delete(cred)
        await db.commit()
    return {"disconnected": True}
