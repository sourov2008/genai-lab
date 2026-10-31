"""Shared pytest fixtures for FastAPI and async SQLAlchemy tests."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator

import httpx
import pytest
from httpx import ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.security import get_current_user_id
from app.db.session import get_db
from app.main import app
from app.models import User
from app.models.base import Base


@pytest.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an in-memory SQLite session with tables and user id 1.

    Yields:
        Function-scoped `AsyncSession` bound to a temporary SQLite database.
    """
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )
    async with session_factory() as session:
        session.add(
            User(
                id=1,
                email="test@clausedesk.local",
                password_hash="!test-not-loginable",
            )
        )
        await session.commit()
        yield session

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def client(test_db: AsyncSession) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Yield an ASGI HTTP client with test database and user overrides.

    Args:
        test_db: Session fixture used in place of `get_db`.

    Yields:
        `httpx.AsyncClient` targeting the FastAPI app in-process.
    """
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield test_db

    async def override_user_id() -> int:
        return 1

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_id] = override_user_id
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client
    app.dependency_overrides.clear()
