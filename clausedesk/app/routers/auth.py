"""HTTP routes for registration and login."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.db.session import get_db
from app.schemas.auth import TokenResponse, UserCreate, UserLogin, UserResponse
from app.services.auth_service import authenticate_user, create_user

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post("/register", response_model=UserResponse)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Register a new user.

    Args:
        user_in: Email and plaintext password.
        db: Request-scoped database session.

    Returns:
        The created user's id and email.

    Raises:
        HTTPException: 400 if the email is already registered.
    """
    try:
        user = await create_user(db, user_in)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return UserResponse.model_validate(user)


@auth_router.post("/login", response_model=TokenResponse)
async def login(
    user_in: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Issue a JWT for a valid email and password.

    Args:
        user_in: Login credentials.
        db: Request-scoped database session.

    Returns:
        Bearer token payload.

    Raises:
        HTTPException: 401 if credentials are invalid.
    """
    user = await authenticate_user(db, user_in.email, user_in.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token)
