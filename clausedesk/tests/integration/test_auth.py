"""Integration tests for registration and login routes."""

from __future__ import annotations

import httpx
import pytest
from httpx import AsyncClient

_NEW_USER = {"email": "new@test.com", "password": "password123"}


async def test_register_user(client: AsyncClient) -> None:
    """POST /auth/register creates a user and returns the email.

    Args:
        client: In-process HTTP client.
    """
    response = await client.post("/auth/register", json=_NEW_USER)
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "new@test.com"


async def test_register_duplicate_email(client: AsyncClient) -> None:
    """POST /auth/register twice with the same email returns 400.

    Args:
        client: In-process HTTP client.
    """
    first = await client.post("/auth/register", json=_NEW_USER)
    assert first.status_code == 200
    second = await client.post("/auth/register", json=_NEW_USER)
    assert second.status_code == 400


async def test_login_success(client: AsyncClient) -> None:
    """POST /auth/login returns a JWT after a valid registration.

    Args:
        client: In-process HTTP client.
    """
    register = await client.post("/auth/register", json=_NEW_USER)
    assert register.status_code == 200
    response = await client.post("/auth/login", json=_NEW_USER)
    assert response.status_code == 200
    body = response.json()
    assert body["access_token"] is not None
    assert body["token_type"] == "bearer"


async def test_login_invalid_password(client: AsyncClient) -> None:
    """POST /auth/login with the wrong password returns 401.

    Args:
        client: In-process HTTP client.
    """
    register = await client.post("/auth/register", json=_NEW_USER)
    assert register.status_code == 200
    response = await client.post(
        "/auth/login",
        json={"email": "new@test.com", "password": "wrongpass"},
    )
    assert response.status_code == 401
