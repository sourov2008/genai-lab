"""HTTP routes for inbound webhook callbacks."""

from __future__ import annotations

import logging

from fastapi import APIRouter
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


class N8nNotifyPayload(BaseModel):
    """Inbound n8n test payload. No business logic yet."""

    message: str
    level: str = Field(default="info")


class N8nNotifyResponse(BaseModel):
    """Acknowledgement that the webhook was accepted."""

    status: str = "received"


@router.post("/n8n/notify", response_model=N8nNotifyResponse)
async def n8n_notify(payload: N8nNotifyPayload) -> N8nNotifyResponse:
    """Accept a dummy notification from n8n to verify connectivity.

    Args:
        payload: JSON body with `message` and optional `level`.

    Returns:
        `{"status": "received"}`.
    """
    logger.info("n8n notify received level=%s message=%s", payload.level, payload.message)
    return N8nNotifyResponse()
