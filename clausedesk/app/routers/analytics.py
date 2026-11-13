"""HTTP routes for usage analytics."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models import Contract, PromptRun, User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/daily-digest")
async def daily_digest(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, int | float]:
    """Return token, cost, and contract counts for the last 24 hours.

    Args:
        db: Request-scoped database session.
        current_user: Authenticated user (auth gate only).

    Returns:
        Aggregated digest for the rolling 24-hour window.
    """
    _ = current_user
    time_24h_ago = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=24)

    runs_row = (
        await db.execute(
            select(
                func.count(PromptRun.id),
                func.sum(PromptRun.input_tokens),
                func.sum(PromptRun.output_tokens),
                func.sum(PromptRun.cost_usd),
            ).where(PromptRun.created_at >= time_24h_ago)
        )
    ).one()
    total_runs, total_input_tokens, total_output_tokens, total_cost_usd = runs_row

    contracts_processed = (
        await db.execute(
            select(func.count(Contract.id)).where(Contract.created_at >= time_24h_ago)
        )
    ).scalar_one()
    contracts_failed = (
        await db.execute(
            select(func.count(Contract.id)).where(
                Contract.created_at >= time_24h_ago,
                Contract.status == "failed",
            )
        )
    ).scalar_one()

    digest: dict[str, int | float] = {
        "total_runs": int(total_runs or 0),
        "total_input_tokens": int(total_input_tokens or 0),
        "total_output_tokens": int(total_output_tokens or 0),
        "total_cost_usd": float(total_cost_usd or 0.0),
        "contracts_processed": int(contracts_processed or 0),
        "contracts_failed": int(contracts_failed or 0),
        "period_hours": 24,
    }
    logger.debug("daily-digest %s", digest)
    return digest
