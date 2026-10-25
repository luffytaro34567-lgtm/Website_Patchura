"""Password hashing, verification, and policy enforcement."""
from __future__ import annotations

import re
from typing import Optional, Tuple
from passlib.context import CryptContext

from app.core.config import settings

# Configure passlib CryptContext using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


def validate_password_strength(password: str) -> Tuple[bool, Optional[str]]:
    """
    Enforces a strict, documented password security policy:
    - Minimum length: 8 characters (configured via settings)
    - Maximum length: 128 characters
    - At least one uppercase letter (A-Z)
    - At least one lowercase letter (a-z)
    - At least one decimal digit (0-9)
    - At least one special symbol (!@#$%^&*()_+-=[]{}|;:,.<>?)
    """
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        return False, f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long."

    if len(password) > settings.PASSWORD_MAX_LENGTH:
        return False, f"Password must not exceed {settings.PASSWORD_MAX_LENGTH} characters."

    if not re.search(r"[A-Z]", password):
        return False, "Password must include at least one uppercase letter (A-Z)."

    if not re.search(r"[a-z]", password):
        return False, "Password must include at least one lowercase letter (a-z)."

    if not re.search(r"\d", password):
        return False, "Password must include at least one numeric digit (0-9)."

    if not re.search(r"[!@#$%^&*()_+\-=\[\]{}|;:,.<>?/~`]", password):
        return False, "Password must include at least one special character (e.g. !@#$%^&*)."

    return True, None
