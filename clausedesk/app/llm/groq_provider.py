"""Groq chat-completions adapter."""

from __future__ import annotations

import logging
import time
import uuid

import groq
from groq import APIConnectionError, APIStatusError, APITimeoutError, AsyncGroq

from app.llm.base import LLMProvider, LLMRequest, LLMResponse, LLMUsage
from app.llm.errors import (
    LLMAuthError,
    LLMBadRequestError,
    LLMError,
    LLMRateLimitError,
    LLMServerError,
    LLMTimeoutError,
)

logger = logging.getLogger(__name__)


class GroqProvider(LLMProvider):
    """LLMProvider backed by the official Groq async SDK."""

    def __init__(self, api_key: str, model: str, timeout_s: float = 30.0) -> None:
        """Create a Groq client for a single model.

        Args:
            api_key: Groq API key.
            model: Model id (for example `llama-3.3-70b-versatile`).
            timeout_s: Per-request timeout in seconds.
        """
        self._client = AsyncGroq(api_key=api_key, timeout=timeout_s)
        self._model = model
        self._timeout_s = timeout_s

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Run a chat completion and map SDK errors to `LLMError` types.

        Args:
            request: Messages and generation parameters.

        Returns:
            Normalized text, usage (cost currently 0.0), and metadata.
        """
        started = time.monotonic()
        request_id = uuid.uuid4().hex[:12]
        messages = [m.model_dump() for m in request.messages]
        create_kwargs: dict = {
            "model": self._model,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }
        if request.response_format is not None:
            create_kwargs["response_format"] = request.response_format
        try:
            raw = await self._client.chat.completions.create(**create_kwargs)
        except groq.APIStatusError as exc:
            self._raise_for_status(exc)
        except (APITimeoutError, APIConnectionError, TimeoutError) as exc:
            raise LLMTimeoutError(f"groq: {exc}") from exc

        latency_ms = int((time.monotonic() - started) * 1000)
        text = raw.choices[0].message.content or ""
        usage = raw.usage
        input_tokens = usage.prompt_tokens if usage is not None else 0
        output_tokens = usage.completion_tokens if usage is not None else 0
        logger.debug("groq complete request_id=%s latency_ms=%s", request_id, latency_ms)
        return LLMResponse(
            text=text,
            model=self._model,
            provider="groq",
            usage=LLMUsage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=0.0,
            ),
            latency_ms=latency_ms,
            request_id=request_id,
        )

    def _raise_for_status(self, exc: APIStatusError) -> None:
        """Map a Groq HTTP error to a typed `LLMError` and raise it."""
        status = exc.status_code
        message = f"groq: {exc.message}"
        if status in {401, 403}:
            raise LLMAuthError(message) from exc
        if status == 429:
            retry_after_s: float | None = None
            if exc.response is not None and "retry-after" in exc.response.headers:
                try:
                    retry_after_s = float(exc.response.headers["retry-after"])
                except ValueError:
                    retry_after_s = None
            raise LLMRateLimitError(message, retry_after_s=retry_after_s) from exc
        if 400 <= status < 500:
            raise LLMBadRequestError(message) from exc
        if status >= 500:
            raise LLMServerError(message) from exc
        raise LLMError(message) from exc
