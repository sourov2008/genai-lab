"""Seed the production demo user (id=1) if it does not exist."""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.db.session import get_session_factory
from app.models import User

logger = logging.getLogger(__name__)


async def seed_prod_user() -> None:
    """Insert `User(id=1)` when the production seed account is missing."""
    factory = get_session_factory()
    async with factory() as session:
        result = await session.execute(select(User).where(User.id == 1))
        user = result.scalar_one_or_none()
        if user is not None:
            logger.info("Production seed user already exists id=%s", user.id)
            return
        session.add(
            User(
                id=1,
                email="prod-seed@clausedesk.local",
                password_hash="!seed-not-loginable",
            )
        )
        await session.commit()
        logger.info("Created production seed user id=1")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(seed_prod_user())
