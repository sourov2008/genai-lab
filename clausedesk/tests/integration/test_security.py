"""Integration tests for contract ownership isolation."""

from __future__ import annotations

import httpx
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.models import Contract, User
from app.models.contract import ContractStatus


async def test_user_cannot_access_other_users_contract(
    client: AsyncClient,
    test_db: AsyncSession,
) -> None:
    """User 1 must not see or fetch a contract owned by user 2.

    Args:
        client: In-process HTTP client authenticated as user 1.
        test_db: Isolated SQLite session.
    """
    assert get_current_user is not None
    test_db.add(
        User(
            id=2,
            email="other@test.com",
            password_hash="!other-not-loginable",
        )
    )
    other_contract = Contract(
        user_id=2,
        filename="other-owner.txt",
        raw_text="secret contract text",
        status=ContractStatus.PENDING.value,
    )
    test_db.add(other_contract)
    await test_db.commit()
    await test_db.refresh(other_contract)

    detail = await client.get(f"/contracts/{other_contract.id}")
    assert detail.status_code in {403, 404}

    listing = await client.get("/contracts/")
    assert listing.status_code == 200
    items = listing.json()["items"]
    owned_ids = [item["id"] for item in items]
    assert other_contract.id not in owned_ids
