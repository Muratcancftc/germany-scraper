"""DB-less auth. A single admin account configured via environment variables
(ADMIN_USERNAME / ADMIN_PASSWORD, with DEFAULT_USER_EMAIL/PASSWORD kept as
backward-compatible aliases). Login issues a JWT (HS256) signed with AUTH_SECRET.
No database, no user store — credentials never live in the source code."""

from __future__ import annotations

import secrets

from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.core.schemas import TokenResponse, UserLogin
from app.core.security.auth import create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _valid_credentials(username: str, password: str) -> bool:
    user_ok = secrets.compare_digest(username.strip().lower(), settings.ADMIN_USERNAME.lower())
    email_ok = secrets.compare_digest(
        username.strip().lower(), settings.DEFAULT_USER_EMAIL.lower()
    )
    pass_ok = secrets.compare_digest(password, settings.ADMIN_PASSWORD)
    return (user_ok or email_ok) and pass_ok


@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin):
    if not _valid_credentials(user_data.username, user_data.password):
        raise HTTPException(401, "Invalid credentials")

    identity = settings.DEFAULT_USER_EMAIL or f"{settings.ADMIN_USERNAME}@example.com"
    token = create_access_token({"user_id": identity, "email": identity, "role": "admin"})
    return TokenResponse(access_token=token, token_type="bearer")
