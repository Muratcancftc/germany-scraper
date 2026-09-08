"""In-memory auth. Users live in a process-local dict (no database). A default
admin is seeded from settings on first use. Tokens are JWT (HS256)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.core.schemas import TokenResponse, UserCreate, UserLogin
from app.core.security.auth import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Process-local user store: email -> password_hash
_users: dict[str, str] = {}
_seeded = False


def _seed_default_user() -> None:
    global _seeded
    if _seeded:
        return
    _seeded = True
    _users[settings.DEFAULT_USER_EMAIL] = hash_password(settings.DEFAULT_USER_PASSWORD)


@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    _seed_default_user()
    email = user_data.email.lower()
    if email in _users:
        raise HTTPException(400, "Email already exists")
    _users[email] = hash_password(user_data.password)
    token = create_access_token({"user_id": email, "email": email})
    return TokenResponse(access_token=token, token_type="bearer")


@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin):
    _seed_default_user()
    email = user_data.email.lower()
    stored_hash = _users.get(email)
    if not stored_hash or not verify_password(user_data.password, stored_hash):
        raise HTTPException(401, "Invalid credentials")
    token = create_access_token({"user_id": email, "email": email})
    return TokenResponse(access_token=token, token_type="bearer")
