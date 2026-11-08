"""Password hashing and JWT helpers for authentication."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext

from app.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """Hash a plaintext password with bcrypt.

    Args:
        password: The password to hash.

    Returns:
        The bcrypt hash string.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a plaintext password against a stored hash.

    Args:
        plain_password: Password supplied by the user.
        hashed_password: Stored bcrypt hash.

    Returns:
        True if the password matches the hash.
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    """Encode a JWT with an expiration from settings.

    Args:
        data: Claims to include in the token (copied before encoding).

    Returns:
        Encoded JWT string.
    """
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt_expire_minutes
    )
    to_encode["exp"] = expire
    return jwt.encode(
        to_encode,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT.

    Args:
        token: Encoded JWT string.

    Returns:
        The decoded claims dictionary.
    """
    settings = get_settings()
    return jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=[settings.jwt_algorithm],
    )


async def get_current_user_id() -> int:
    """Return the authenticated user id.

    Mock implementation until JWT auth is wired into dependencies.

    Returns:
        Hardcoded seed user id `1`.
    """
    return 1
