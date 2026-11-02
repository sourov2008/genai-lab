"""Quote verification and clause review-status routing."""

from __future__ import annotations

from app.models import Contract
from app.models.clause import ClauseStatus


def verify_clause(contract: Contract, item: dict) -> dict | None:
    """Verify an extracted clause quote against the contract source.

    Args:
        contract: Contract whose `raw_text` is the source of truth.
        item: LLM clause object with `quote`, optional `confidence` and `clause_type`.

    Returns:
        Normalized clause fields, or `None` if `quote` is missing.
    """
    quote = item.get("quote")
    if not quote:
        return None
    verified = quote in contract.raw_text
    confidence = item.get("confidence", 0.0) or 0.0
    status = (
        ClauseStatus.AUTO_ACCEPTED.value
        if (verified and confidence >= 0.7)
        else ClauseStatus.REVIEW.value
    )
    return {
        "clause_type": item.get("clause_type", "unknown"),
        "quote": quote,
        "confidence": confidence,
        "verified": verified,
        "status": status,
    }
