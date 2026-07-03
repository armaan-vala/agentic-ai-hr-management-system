"""
Supabase Auth Admin API (server-side, uses the SECRET key).

Used by the admin 'add employee' flow to create a login for a new employee.
The new-style `sb_secret_...` key authorizes the admin endpoints.
"""
from __future__ import annotations

import secrets

import httpx

from app.core.config import settings


def _admin_url(path: str = "") -> str:
    return f"{settings.supabase_url.rstrip('/')}/auth/v1/admin/users{path}"


def _headers() -> dict:
    key = settings.supabase_secret_key
    return {"apikey": key, "Authorization": f"Bearer {key}"}


def generate_password() -> str:
    """A reasonably strong temporary password for a new employee."""
    return secrets.token_urlsafe(10)


async def create_auth_user(email: str, password: str) -> str:
    """Create a confirmed auth user and return its UUID (string)."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            _admin_url(),
            headers=_headers(),
            json={"email": email, "password": password, "email_confirm": True},
        )
        if resp.status_code >= 400:
            raise RuntimeError(f"Supabase admin error {resp.status_code}: {resp.text[:200]}")
        return resp.json()["id"]


async def delete_auth_user(user_id: str) -> None:
    """Remove an auth user (used for cleanup / deactivation)."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        await client.delete(_admin_url(f"/{user_id}"), headers=_headers())
