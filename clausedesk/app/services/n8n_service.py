"""Outbound n8n webhook notifications for extraction errors."""

from __future__ import annotations

import logging

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


async def send_error_alert(contract_id: int, error_message: str) -> None:
    """POST an error payload to n8n. Skip or swallow failures if n8n is unset or down.

    Args:
        contract_id: Contract that failed processing.
        error_message: Human-readable error text for the alert.
    """
    settings = get_settings()
    if not settings.n8n_webhook_url:
        logger.warning("N8N_WEBHOOK_URL is empty; skipping error alert")
        return

    payload = {
        "contract_id": contract_id,
        "error": error_message,
        "level": "error",
        "source": "ClauseDesk API",
    }
    try:
        async with httpx.AsyncClient() as client:
            await client.post(settings.n8n_webhook_url, json=payload)
    except Exception:
        logger.exception("Failed to send n8n error alert for contract_id=%s", contract_id)
