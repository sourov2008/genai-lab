"""Integration tests for contract upload and list routes."""

from __future__ import annotations

import httpx
import pytest
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Base, Contract, User


async def _ensure_seed_user(test_db: AsyncSession) -> None:
    user = await test_db.get(User, 1)
    if user is None:
        test_db.add(
            User(
                id=1,
                email="test@clausedesk.local",
                password_hash="!test-not-loginable",
            )
        )
        await test_db.commit()


async def _clear_user_contracts(test_db: AsyncSession) -> None:
    await test_db.execute(delete(Contract).where(Contract.user_id == 1))
    await test_db.commit()


async def test_create_contract(client: AsyncClient, test_db: AsyncSession) -> None:
    """POST a contract and expect a pending summary payload.

    Args:
        client: In-process HTTP client.
        test_db: Isolated SQLite session.
    """
    await _ensure_seed_user(test_db)
    await _clear_user_contracts(test_db)

    response = await client.post(
        "/contracts/",
        data={"filename": "test.pdf", "raw_text": "hello"},
    )

    assert response.status_code in {200, 201}
    body = response.json()
    assert body["filename"] == "test.pdf"
    assert body["status"] == "pending"


async def test_get_contracts(client: AsyncClient, test_db: AsyncSession) -> None:
    """POST one contract then GET the list with a single item.

    Args:
        client: In-process HTTP client.
        test_db: Isolated SQLite session.
    """
    await _ensure_seed_user(test_db)
    await _clear_user_contracts(test_db)

    await client.post(
        "/contracts/",
        data={"filename": "test.pdf", "raw_text": "hello"},
    )
    response = await client.get("/contracts/")

    assert response.status_code == 200
    assert len(response.json()) == 1
