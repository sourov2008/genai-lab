"""Async SQLAlchemy engine and session factory."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Return a process-wide async engine, creating it on first use.

    Returns:
        Shared `AsyncEngine` bound to `Settings.database_url`.
    """
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            pool_pre_ping=True,
        )
        logger.debug("Created async engine")
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return a process-wide session factory, creating it on first use.

    Returns:
        `async_sessionmaker` that produces `AsyncSession` instances.
    """
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            expire_on_commit=False,
            class_=AsyncSession,
        )
        logger.debug("Created async session factory")
    return _session_factory


async def get_db() -> AsyncIterator[AsyncSession]:
    """Yield an AsyncSession for FastAPI Depends. Rollback on error.

    Yields:
        An `AsyncSession` for the current request.

    Raises:
        Exception: Re-raised after rollback if the request fails.
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
