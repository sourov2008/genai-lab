"""Typed errors for LLM provider calls."""

from __future__ import annotations


class LLMError(Exception):
    """Base error for all LLM provider failures."""


class LLMAuthError(LLMError):
    """Raised on HTTP 401 or 403. Do not retry; fix credentials."""


class LLMBadRequestError(LLMError):
    """Raised on HTTP 400. Do not retry; fix the prompt or request."""


class LLMRateLimitError(LLMError):
    """Raised on HTTP 429. Retry after `retry_after_s` when provided."""

    def __init__(
        self,
        message: str = "",
        retry_after_s: float | None = None,
    ) -> None:
        """Store an optional Retry-After delay in seconds.

        Args:
            message: Human-readable error description.
            retry_after_s: Seconds to wait before retrying, if known.
        """
        super().__init__(message)
        self.retry_after_s = retry_after_s


class LLMServerError(LLMError):
    """Raised on HTTP 5xx. Retry with exponential backoff."""


class LLMTimeoutError(LLMError):
    """Raised when the provider call times out or the network fails."""
