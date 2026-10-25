"""Cryptographic token generation, hashing, and JWT handling."""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple, Union

from jose import JWTError, jwt

from app.core.config import settings


def create_access_token(
    user_id: Optional[str] = None,
    role: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
    data: Optional[Dict[str, Any]] = None,
) -> str:
    """Create a short-lived signed JWT access token."""
    if data:
        user_id = user_id or data.get("sub")
        role = role or data.get("role", "client")

    if not user_id:
        raise ValueError("user_id or data['sub'] must be provided")
    if not role:
        role = "client"

    now = datetime.now(timezone.utc)
    if expires_delta is not None:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: Dict[str, Any] = {
        "sub": user_id,
        "role": role,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "jti": secrets.token_hex(16),
    }

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate a signed JWT access token."""
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )


def generate_refresh_token() -> Tuple[str, str]:
    """
    Generate a cryptographically secure random refresh token secret.
    Returns:
        tuple[raw_token, token_hash]:
        - raw_token: Delivered once to client
        - token_hash: SHA-256 hash stored in DB to prevent plaintext exposure
    """
    raw_token = secrets.token_urlsafe(48)
    token_hash = hash_refresh_token(raw_token)
    return raw_token, token_hash


def hash_refresh_token(raw_token: Union[str, Tuple[str, str]]) -> str:
    """Compute the SHA-256 hash of a raw refresh token."""
    if isinstance(raw_token, tuple):
        return raw_token[1]
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
