"""Smoke-test embeddings by ranking a few stored clause quotes."""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import get_session_factory
from app.llm.embeddings import cosine_similarity, get_embedding
from app.models import Clause

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Embed a query and the first five clauses, then print ranked scores."""
    query = "What happens if either party wants to end the agreement?"
    query_vec = await get_embedding(query)
    factory = get_session_factory()
    async with factory() as db:
        result = await db.execute(select(Clause).limit(5))
        clauses = result.scalars().all()

    if not clauses:
        logger.info("No clauses in the database to compare.")
        return

    scored: list[tuple[float, Clause]] = []
    for clause in clauses:
        clause_vec = await get_embedding(clause.quote)
        score = cosine_similarity(query_vec, clause_vec)
        scored.append((score, clause))
        preview = clause.quote[:100]
        print(f"Similarity: {score:.3f} | Clause: {preview}...")

    scored.sort(key=lambda item: item[0], reverse=True)
    top_score, top_clause = scored[0]
    print(
        f"Top match: Similarity: {top_score:.3f} | "
        f"Clause: {top_clause.quote[:100]}..."
    )


if __name__ == "__main__":
    asyncio.run(main())
