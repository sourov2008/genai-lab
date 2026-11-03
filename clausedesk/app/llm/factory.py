"""Construct the configured `LLMProvider` from settings."""

from __future__ import annotations

from app.core.config import Settings, get_settings
from app.llm.base import LLMProvider
from app.llm.groq_provider import GroqProvider
from app.llm.openai_provider import OpenAIProvider


def make_llm_provider(settings: Settings) -> LLMProvider:
    """Return the LLM provider named in settings.

    Args:
        settings: Application settings including provider and credentials.

    Returns:
        An `OpenAIProvider` when `llm_provider` is `openai`, or a
        `GroqProvider` when `llm_provider` is `groq`.

    Raises:
        ValueError: If the provider name is not supported.
    """
    if settings.llm_provider == "openai":
        return OpenAIProvider(
            settings.openai_api_key,
            settings.openai_model,
            settings.llm_timeout_s,
        )
    elif settings.llm_provider == "groq":
        return GroqProvider(
            settings.groq_api_key,
            settings.groq_model,
            settings.llm_timeout_s,
        )
    raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")


def get_llm() -> LLMProvider:
    """Return the process LLM provider for FastAPI `Depends`."""
    return make_llm_provider(get_settings())
