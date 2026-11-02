"""Construct the configured `LLMProvider` from settings."""

from __future__ import annotations

from app.core.config import Settings
from app.llm.base import LLMProvider
from app.llm.openai_provider import OpenAIProvider


def make_llm_provider(settings: Settings) -> LLMProvider:
    """Return the LLM provider named in settings.

    Args:
        settings: Application settings including provider and credentials.

    Returns:
        An `OpenAIProvider` when `llm_provider` is `openai`.

    Raises:
        ValueError: If the provider name is not supported.
    """
    if settings.llm_provider == "openai":
        return OpenAIProvider(
            settings.openai_api_key,
            settings.openai_model,
            settings.llm_timeout_s,
        )
    raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
