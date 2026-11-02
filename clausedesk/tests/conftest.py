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
from app.llm.base import LLMProvider, LLMRequest, LLMResponse, LLMUsage
from app.llm.factory import get_llm
from app.main import app
from app.models import User
from app.models.base import Base


class FakeLLMProvider(LLMProvider):
    """In-memory LLM that returns a verified termination clause. No network."""

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Return a fixed JSON extraction payload.

        Args:
            request: Incoming completion request; must request JSON mode.

        Returns:
            Fake `LLMResponse` with one termination clause.
        """
        assert request.response_format == {"type": "json_object"}
        return LLMResponse(
            text='{"clauses": [{"clause_type": "termination", "quote": "test", "confidence": 0.9}]}',
            model="fake",
            provider="fake",
            usage=LLMUsage(input_tokens=0, output_tokens=0, cost_usd=0.0),
            latency_ms=0,
            request_id="fake-request",
        )


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
def override_llm() -> FakeLLMProvider:
    """Replace `get_llm` with `FakeLLMProvider` for the test.

    Yields:
        The fake provider registered on the FastAPI app.
    """
    provider = FakeLLMProvider()

    def _get_llm() -> LLMProvider:
        return provider

    app.dependency_overrides[get_llm] = _get_llm
    return provider


@pytest.fixture
async def client(
    test_db: AsyncSession,
    override_llm: FakeLLMProvider,
) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Yield an ASGI HTTP client with test database, user, and LLM overrides.

    Args:
        test_db: Session fixture used in place of `get_db`.
        override_llm: Fake LLM registered for `get_llm`.

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
