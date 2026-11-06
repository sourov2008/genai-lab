"""Unit tests for `FallbackProvider` retryable vs non-retryable errors."""

from __future__ import annotations

import pytest

from app.llm.base import LLMProvider, LLMRequest, LLMResponse, LLMUsage, Message
from app.llm.errors import LLMAuthError, LLMServerError
from app.llm.fallback import FallbackProvider

_SUCCESS = LLMResponse(
    text='{"clauses": []}',
    model="mock",
    provider="fallback",
    usage=LLMUsage(input_tokens=1, output_tokens=1, cost_usd=0.0),
    latency_ms=1,
    request_id="fallback-ok",
)


class MockFailingProvider(LLMProvider):
    """Primary that always raises a retryable server error."""

    async def complete(self, request: LLMRequest) -> LLMResponse:
        raise LLMServerError("primary 500")


class MockSuccessProvider(LLMProvider):
    """Secondary that always returns a valid completion."""

    async def complete(self, request: LLMRequest) -> LLMResponse:
        return _SUCCESS


class MockAuthFailingProvider(LLMProvider):
    """Primary that always raises a non-retryable auth error."""

    async def complete(self, request: LLMRequest) -> LLMResponse:
        raise LLMAuthError("primary 401")


def _request() -> LLMRequest:
    return LLMRequest(messages=[Message(role="user", content="hello")])


async def test_fallback_provider_uses_secondary_on_server_error() -> None:
    """Return the fallback completion when the primary raises `LLMServerError`."""
    provider = FallbackProvider(MockFailingProvider(), MockSuccessProvider())
    response = await provider.complete(_request())
    assert response == _SUCCESS
    assert response.provider == "fallback"


async def test_fallback_provider_does_not_catch_auth_error() -> None:
    """Propagate `LLMAuthError` from the primary without calling fallback."""
    provider = FallbackProvider(MockAuthFailingProvider(), MockSuccessProvider())
    with pytest.raises(LLMAuthError):
        await provider.complete(_request())
