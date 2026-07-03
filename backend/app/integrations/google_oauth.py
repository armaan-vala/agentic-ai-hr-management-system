"""
Google OAuth + Gmail send, via plain HTTP (httpx) — no heavy Google SDK.

Per-user flow:
  1. build_auth_url(state) -> send the user to Google to consent.
  2. exchange_code(code) -> {refresh_token, access_token, email}.
  3. store the refresh token (encrypted) keyed by our user id.
  4. later, refresh_access_token(refresh_token) -> short-lived access token.
  5. send_gmail(access_token, ...) -> sends from the user's own Gmail.
"""
from __future__ import annotations

import base64
import json
from email.message import EmailMessage
from urllib.parse import urlencode

import httpx
from cryptography.fernet import Fernet

from app.core.config import settings

AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
GMAIL_SEND = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/gmail.send",
]


# --- token-at-rest encryption -------------------------------------------------
def _fernet() -> Fernet:
    return Fernet(settings.token_encryption_key.encode())


def encrypt(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()


def decrypt(value: str) -> str:
    return _fernet().decrypt(value.encode()).decode()


# --- OAuth --------------------------------------------------------------------
def build_auth_url(state: str) -> str:
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",   # get a refresh token
        "prompt": "consent",        # force refresh token even on re-connect
        "include_granted_scopes": "true",
        "state": state,
    }
    return f"{AUTH_ENDPOINT}?{urlencode(params)}"


def _email_from_id_token(id_token: str) -> str:
    """Read the email claim from Google's id_token (already trusted — came over TLS)."""
    try:
        payload_b64 = id_token.split(".")[1]
        payload_b64 += "=" * (-len(payload_b64) % 4)  # pad
        data = json.loads(base64.urlsafe_b64decode(payload_b64))
        return data.get("email", "")
    except Exception:
        return ""


async def exchange_code(code: str) -> dict:
    """Swap the auth code for tokens. Returns {refresh_token, access_token, email}."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            TOKEN_ENDPOINT,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        resp.raise_for_status()
        tok = resp.json()
    return {
        "refresh_token": tok.get("refresh_token", ""),
        "access_token": tok.get("access_token", ""),
        "email": _email_from_id_token(tok.get("id_token", "")),
    }


async def refresh_access_token(refresh_token: str) -> str:
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            TOKEN_ENDPOINT,
            data={
                "refresh_token": refresh_token,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "grant_type": "refresh_token",
            },
        )
        resp.raise_for_status()
        return resp.json()["access_token"]


# --- Gmail --------------------------------------------------------------------
async def send_gmail(
    access_token: str, *, to: str, subject: str, body: str, sender: str = "me"
) -> dict:
    msg = EmailMessage()
    msg["To"] = to
    msg["Subject"] = subject
    if sender != "me":
        msg["From"] = sender
    msg.set_content(body)
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            GMAIL_SEND,
            headers={"Authorization": f"Bearer {access_token}"},
            json={"raw": raw},
        )
        resp.raise_for_status()
        return resp.json()
