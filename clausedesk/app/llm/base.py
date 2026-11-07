"""Provider-agnostic LLM request, response, and provider ABC."""

from __future__ import annotations

import abc
import typing

from pydantic import BaseModel, ConfigDict


class Message(BaseModel):
    """A single chat message sent to an LLM."""

    model_config = ConfigDict(extra="allow")

    role: str
    content: str | None = None
    tool_calls: list[dict] | None = None
    tool_call_id: str | None = None
    name: str | None = None


class LLMRequest(BaseModel):
    """Parameters for one completion call.

    When using OpenAI structured outputs, `response_format` must include a
    JSON schema with ``additionalProperties: false`` and every property listed
    in ``required``. The extraction service builds that schema on the next step.
    """

    messages: list[Message]
    temperature: float = 0.0
    max_tokens: int = 1024
    response_format: dict | None = None
    tools: list[dict] | None = None


class LLMUsage(BaseModel):
    """Token counts and estimated cost for one call."""

    input_tokens: int
    output_tokens: int
    cost_usd: float


class LLMResponse(BaseModel):
    """Normalized completion result from any provider."""

    text: str
    model: str
    provider: str
    usage: LLMUsage
    latency_ms: int
    request_id: str
    tool_calls: list[dict] | None = None


class LLMProvider(abc.ABC):
    """Async interface implemented by OpenAI, Groq, and fakes."""

    @abc.abstractmethod
    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Run a chat completion.

        Args:
            request: Messages and generation parameters.

        Returns:
            Provider-normalized text, usage, and metadata.
        """
        ...
