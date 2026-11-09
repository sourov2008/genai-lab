"""Reset Postgres identity sequences after manual id inserts."""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def _rewrite_database_url(database_url: str) -> str:
    """Return an asyncpg URL for SQLAlchemy."""
    if database_url.startswith("postgres://"):
        return "postgresql+asyncpg://" + database_url.removeprefix("postgres://")
    if database_url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + database_url.removeprefix("postgresql://")
    return database_url


async def sync_sequences() -> None:
    """Align `users_id_seq` with the current max `users.id`."""
    settings = get_settings()
    database_url = os.environ.get("DATABASE_URL", settings.database_url)
    database_url = _rewrite_database_url(database_url)
    engine = create_async_engine(database_url, pool_pre_ping=True)
    try:
        async with engine.begin() as connection:
            await connection.execute(
                text(
                    "SELECT setval('users_id_seq', "
                    "COALESCE((SELECT MAX(id) FROM users), 1), "
                    "(SELECT COUNT(*) > 0 FROM users));"
                )
            )
        logger.info("Reset users_id_seq to match MAX(users.id)")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(sync_sequences())
