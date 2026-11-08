"""User registration and password authentication."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.models import User
from app.schemas.auth import UserCreate


async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    """Create a user if the email is not already registered.

    Args:
        db: Active async database session.
        user_in: Email and plaintext password.

    Returns:
        The persisted `User`.

    Raises:
        ValueError: If the email is already registered.
    """
    result = await db.execute(select(User).where(User.email == user_in.email))
    existing = result.scalar_one_or_none()
    if existing is not None:
        raise ValueError("Email already registered")
    user = User(
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str,
) -> User | None:
    """Return the user if email and password match.

    Args:
        db: Active async database session.
        email: Account email.
        password: Plaintext password to verify.

    Returns:
        The matching `User`, or `None` if the email is missing or the
        password is wrong.
    """
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user
