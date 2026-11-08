"""Pydantic schemas for registration, login, and JWT responses."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Payload for creating a new user."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)


class UserLogin(BaseModel):
    """Payload for email and password login."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)


class TokenResponse(BaseModel):
    """JWT returned after successful authentication."""

    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Public user fields returned after registration."""

    id: int
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)
