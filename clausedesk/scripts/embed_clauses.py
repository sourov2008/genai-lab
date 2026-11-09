"""Backfill embeddings for clauses that do not have one yet."""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import get_engine, get_session_factory
from app.llm.embeddings import get_embedding
from app.models import Clause

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

_BATCH_SIZE = 10


async def embed_existing_clauses() -> None:
    """Embed every `Clause` whose `embedding` is still NULL."""
    factory = get_session_factory()
    engine = get_engine()
    embedded = 0
    try:
        async with factory() as db:
            result = await db.execute(
                select(Clause).where(Clause.embedding.is_(None))
            )
            clauses = result.scalars().all()
            if not clauses:
                logger.info("Embedded 0 clauses")
                return
            for clause in clauses:
                clause.embedding = await get_embedding(clause.quote)
                embedded += 1
                if embedded % _BATCH_SIZE == 0:
                    await db.commit()
                    logger.info("Embedded %s clauses", embedded)
            await db.commit()
            logger.info("Embedded %s clauses", embedded)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(embed_existing_clauses())
