"""Database-backed tools for an extraction-review agent."""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Clause, Contract
from app.models.clause import ClauseStatus

logger = logging.getLogger(__name__)

TOOL_SCHEMAS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "get_clause",
            "description": (
                "Fetch one extracted clause from a contract by clause type "
                "(for example termination or governing_law)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "contract_id": {
                        "type": "integer",
                        "description": "Database id of the contract.",
                    },
                    "clause_type": {
                        "type": "string",
                        "description": "Clause type key, such as termination.",
                    },
                },
                "required": ["contract_id", "clause_type"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_similar_clauses",
            "description": (
                "Search stored clause quotes for a substring. Stub for later RAG."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Text to find inside clause quotes.",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "flag_for_review",
            "description": (
                "Set a clause status to review and record a human-readable reason."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "clause_id": {
                        "type": "integer",
                        "description": "Database id of the clause.",
                    },
                    "reason": {
                        "type": "string",
                        "description": "Why the clause should be reviewed.",
                    },
                },
                "required": ["clause_id", "reason"],
            },
        },
    },
]


async def get_clause(
    db: AsyncSession,
    contract_id: int,
    clause_type: str,
) -> dict:
    """Return one clause of the given type on a contract.

    Args:
        db: Active async database session.
        contract_id: Parent contract primary key.
        clause_type: Extracted clause type key.

    Returns:
        `clause_type`, `quote`, and `status`, or an error dict if missing.
    """
    result = await db.execute(
        select(Clause)
        .join(Contract, Clause.contract_id == Contract.id)
        .where(
            Clause.contract_id == contract_id,
            Clause.clause_type == clause_type,
        )
    )
    clause = result.scalars().first()
    if clause is None:
        return {"error": "Clause not found"}
    return {
        "clause_type": clause.clause_type,
        "quote": clause.quote,
        "status": clause.status,
    }


async def search_similar_clauses(db: AsyncSession, query: str) -> list[dict]:
    """Return up to three clauses whose quotes contain `query`.

    Args:
        db: Active async database session.
        query: Substring matched with case-insensitive `ilike`.

    Returns:
        Dicts with `contract_id`, `clause_type`, and `quote`.
    """
    result = await db.execute(
        select(Clause)
        .where(Clause.quote.ilike(f"%{query}%"))
        .limit(3)
    )
    clauses = result.scalars().all()
    return [
        {
            "contract_id": clause.contract_id,
            "clause_type": clause.clause_type,
            "quote": clause.quote,
        }
        for clause in clauses
    ]


async def flag_for_review(
    db: AsyncSession,
    clause_id: int,
    reason: str,
) -> dict:
    """Mark a clause as needing human review.

    Args:
        db: Active async database session.
        clause_id: Clause primary key.
        reason: Note stored only in the tool response (not a DB column).

    Returns:
        Success payload, or an error dict if the clause is missing.
    """
    result = await db.execute(select(Clause).where(Clause.id == clause_id))
    clause = result.scalar_one_or_none()
    if clause is None:
        return {"error": "Clause not found"}
    clause.status = ClauseStatus.REVIEW.value
    await db.commit()
    logger.info("Flagged clause_id=%s for review: %s", clause_id, reason)
    return {
        "status": "success",
        "message": f"Clause {clause_id} flagged for review. Reason: {reason}",
    }
