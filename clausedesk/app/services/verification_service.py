"""Quote verification and clause review-status routing."""

from __future__ import annotations

import difflib
import logging

from app.models import Contract
from app.models.clause import ClauseStatus

logger = logging.getLogger(__name__)

KEYWORDS: dict[str, list[str]] = {
    "termination": ["terminat", "cancel", "expire", "lapse"],
    "liability_cap": ["liab", "cap", "limit", "exceed"],
    "governing_law": ["law", "govern", "jurisdiction", "court"],
    "confidentiality": ["confidential", "disclos", "receiving party", "proprietary"],
    "payment_terms": ["pay", "fee", "invoice", "amount", "currency"],
    "ip_ownership": ["intellectual property", "ip", "ownership", "copyright", "patent"],
    "renewal": ["renew", "extend", "successive term"],
    "non_compete": ["compete", "competitor", "solicit", "restrict"],
}


def _best_sliding_ratio(quote: str, text: str) -> float:
    """Return the highest SequenceMatcher ratio of `quote` vs windows of `text`.

    Args:
        quote: Extracted clause quote.
        text: Full contract source text.

    Returns:
        Best similarity ratio in ``[0.0, 1.0]``.
    """
    if not quote or not text:
        return 0.0
    window = len(quote)
    if len(text) < window:
        return difflib.SequenceMatcher(None, quote, text).ratio()
    matcher = difflib.SequenceMatcher()
    matcher.set_seq2(quote)
    best = 0.0
    last_start = len(text) - window
    for start in range(last_start + 1):
        matcher.set_seq1(text[start : start + window])
        ratio = matcher.ratio()
        if ratio > best:
            best = ratio
            if best > 0.90:
                return best
    return best


def verify_clause(contract: Contract, item: dict) -> dict | None:
    """Verify an extracted clause quote against the contract source.

    Step 1 exact-matches the quote in `raw_text`. Step 2 requires a type
    keyword when the quote is an exact match. Step 3 fuzzy-matches typos
    (ratio > 0.90) but still leaves `verified` false so a human reviews.

    Args:
        contract: Contract whose `raw_text` is the source of truth.
        item: LLM clause object with `quote`, optional `confidence` and `clause_type`.

    Returns:
        Normalized clause fields, or `None` if `quote` is missing.
    """
    quote = item.get("quote")
    if not quote:
        return None
    clause_type = item.get("clause_type", "unknown")
    exact_match = quote in contract.raw_text
    verified = exact_match

    if exact_match:
        keywords = KEYWORDS.get(clause_type, [])
        if keywords:
            quote_lower = quote.lower()
            if not any(keyword in quote_lower for keyword in keywords):
                verified = False
                logger.info(
                    "Semantic check failed for clause_type=%s; quote lacks keywords",
                    clause_type,
                )
    else:
        ratio = _best_sliding_ratio(quote, contract.raw_text)
        if ratio > 0.90:
            verified = False
            logger.info(
                "Fuzzy match ratio=%.3f for clause_type=%s; sending to review",
                ratio,
                clause_type,
            )

    confidence = item.get("confidence", 0.0) or 0.0
    status = (
        ClauseStatus.AUTO_ACCEPTED.value
        if (verified is True and confidence >= 0.7)
        else ClauseStatus.REVIEW.value
    )
    return {
        "clause_type": clause_type,
        "quote": quote,
        "confidence": confidence,
        "verified": verified,
        "status": status,
    }
