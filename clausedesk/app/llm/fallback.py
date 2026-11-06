"""Primary-then-secondary LLM provider for transient failures."""

from __future__ import annotations

import logging

from app.llm.base import LLMProvider, LLMRequest, LLMResponse
from app.llm.errors import LLMRateLimitError, LLMServerError, LLMTimeoutError

logger = logging.getLogger(__name__)


class FallbackProvider(LLMProvider):
    """Try the primary provider, then the fallback on retryable errors."""

    def __init__(self, primary: LLMProvider, fallback: LLMProvider) -> None:
        """Store the primary and secondary adapters.

        Args:
            primary: Provider tried first (typically OpenAI).
            fallback: Provider used on 5xx, 429, or timeout (typically Groq).
        """
        self.primary = primary
        self.fallback = fallback

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Complete via primary, then fallback on server, rate-limit, or timeout.

        Auth and bad-request errors propagate; fallback cannot fix those.

        Args:
            request: Messages and generation parameters.

        Returns:
            Normalized completion from primary or fallback.
        """
        try:
            return await self.primary.complete(request)
        except (LLMServerError, LLMRateLimitError, LLMTimeoutError) as exc:
            logger.warning(
                "Primary provider failed (%s). Falling back to secondary provider.",
                exc,
            )
            return await self.fallback.complete(request)
