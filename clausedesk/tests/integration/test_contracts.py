"""Integration tests for contract upload and list routes."""

from __future__ import annotations

import httpx
import pytest
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Base, Contract, User
from app.services import extraction_service


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
    body = response.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1


async def test_get_contract_not_found(client: AsyncClient) -> None:
    """GET a missing contract id and expect 404.

    Args:
        client: In-process HTTP client.
    """
    response = await client.get("/contracts/9999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Contract not found"


async def test_delete_contract(client: AsyncClient, test_db: AsyncSession) -> None:
    """DELETE a created contract and expect it to be gone.

    Args:
        client: In-process HTTP client.
        test_db: Isolated SQLite session.
    """
    await _ensure_seed_user(test_db)

    created = await client.post(
        "/contracts/",
        data={"filename": "test.pdf", "raw_text": "hello"},
    )
    contract_id = created.json()["id"]

    deleted = await client.delete(f"/contracts/{contract_id}")
    assert deleted.status_code == 204

    missing = await client.get(f"/contracts/{contract_id}")
    assert missing.status_code == 404


async def test_update_contract(client: AsyncClient, test_db: AsyncSession) -> None:
    """PATCH filename and keep the original raw_text.

    Args:
        client: In-process HTTP client.
        test_db: Isolated SQLite session.
    """
    await _ensure_seed_user(test_db)
    original_raw_text = "hello"
    created = await client.post(
        "/contracts/",
        data={"filename": "test.pdf", "raw_text": original_raw_text},
    )
    contract_id = created.json()["id"]

    response = await client.patch(
        f"/contracts/{contract_id}",
        json={"filename": "updated.pdf"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["filename"] == "updated.pdf"
    assert body["raw_text"] == original_raw_text


async def test_duplicate_filename_returns_409(
    client: AsyncClient,
    test_db: AsyncSession,
) -> None:
    """PATCH a contract to a filename already used by the same user.

    Args:
        client: In-process HTTP client.
        test_db: Isolated SQLite session.
    """
    await _ensure_seed_user(test_db)
    await client.post(
        "/contracts/",
        data={"filename": "duplicate.pdf", "raw_text": "first"},
    )
    second = await client.post(
        "/contracts/",
        data={"filename": "other.pdf", "raw_text": "second"},
    )
    second_id = second.json()["id"]

    response = await client.patch(
        f"/contracts/{second_id}",
        json={"filename": "duplicate.pdf"},
    )

    assert response.status_code == 409
    detail = response.json()["detail"].lower()
    assert "already exists" in detail or "duplicate" in detail


async def test_pagination(client: AsyncClient, test_db: AsyncSession) -> None:
    """GET a middle page when three contracts exist.

    Args:
        client: In-process HTTP client.
        test_db: Isolated SQLite session.
    """
    await _ensure_seed_user(test_db)
    await _clear_user_contracts(test_db)
    for name in ("a.pdf", "b.pdf", "c.pdf"):
        await client.post(
            "/contracts/",
            data={"filename": name, "raw_text": "hello"},
        )

    response = await client.get("/contracts/", params={"limit": 2, "offset": 1})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert body["limit"] == 2
    assert body["offset"] == 1
    assert len(body["items"]) == 2


async def test_filter_by_status(client: AsyncClient, test_db: AsyncSession) -> None:
    """GET only contracts whose status is ready.

    Args:
        client: In-process HTTP client.
        test_db: Isolated SQLite session.
    """
    await _ensure_seed_user(test_db)
    await _clear_user_contracts(test_db)
    await client.post(
        "/contracts/",
        data={"filename": "pending.pdf", "raw_text": "hello"},
    )
    ready = await client.post(
        "/contracts/",
        data={"filename": "ready.pdf", "raw_text": "hello"},
    )
    await client.patch(
        f"/contracts/{ready.json()['id']}",
        json={"status": "ready"},
    )

    response = await client.get("/contracts/", params={"status": "ready"})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["status"] == "ready"


async def test_extract_contract(client: AsyncClient, test_db: AsyncSession) -> None:
    """POST extract and expect one verified termination clause from the fake LLM.

    Args:
        client: In-process HTTP client.
        test_db: Isolated SQLite session.
    """
    await _ensure_seed_user(test_db)
    await _clear_user_contracts(test_db)
    created = await client.post(
        "/contracts/",
        data={
            "filename": "extract.pdf",
            "raw_text": "This is a test for termination.",
        },
    )
    contract_id = created.json()["id"]

    response = await client.post(f"/contracts/{contract_id}/extract")

    assert response.status_code == 200
    clauses = response.json()
    assert len(clauses) == 1
    assert clauses[0]["clause_type"] == "termination"
    assert clauses[0]["verified"] is True




