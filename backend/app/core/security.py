"""
Authentication — verify Supabase-issued JWTs and resolve the current user.

Supabase signs access tokens with an asymmetric key (ECC P-256 = ES256). We fetch
the public keys from the project's JWKS endpoint and verify against them, so no
shared secret is needed. PyJWKClient caches the keys after the first fetch.
"""
from __future__ import annotations

import uuid

import jwt
from fastapi import Depends, Header, HTTPException, status
from fastapi.concurrency import run_in_threadpool
from jwt import PyJWKClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models.company import Company
from app.models.user import Role, User

_jwk_client = PyJWKClient(settings.jwks_url)

# Supabase access-token constants.
_AUDIENCE = "authenticated"
_ALGORITHMS = ["ES256", "RS256"]


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


async def _decode_token(token: str) -> dict:
    try:
        signing_key = await run_in_threadpool(
            _jwk_client.get_signing_key_from_jwt, token
        )
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=_ALGORITHMS,
            audience=_AUDIENCE,
            options={"verify_exp": True},
        )
    except jwt.PyJWTError as exc:
        raise _unauthorized(f"Invalid token: {exc}") from exc


async def get_current_user(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """FastAPI dependency: validate the bearer token and return our User row.

    First-time login auto-provisions a Company + admin User so the app is usable
    before the admin 'add employee' flow exists. Later, employees are pre-created
    by that flow, so provisioning won't trigger for them.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise _unauthorized("Missing bearer token")
    token = authorization.split(" ", 1)[1].strip()

    payload = await _decode_token(token)
    sub = payload.get("sub")
    email = payload.get("email", "")
    if not sub:
        raise _unauthorized("Token missing subject")

    user_id = uuid.UUID(sub)
    user = await db.get(User, user_id)
    if user is not None:
        return user

    # --- auto-provision on first login ---
    company = Company(name=(email.split("@")[0] or "My Company") + " (workspace)")
    db.add(company)
    await db.flush()  # get company.id
    user = User(
        id=user_id,
        company_id=company.id,
        email=email,
        full_name=email.split("@")[0],
        role=Role.admin,  # first user of a workspace is its admin
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
