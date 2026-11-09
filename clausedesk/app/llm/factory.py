"""Construct the configured `LLMProvider` from settings."""

from __future__ import annotations

from app.core.config import Settings, get_settings
from app.llm.base import LLMProvider
from app.llm.fallback import FallbackProvider
from app.llm.groq_provider import GroqProvider
from app.llm.openai_provider import OpenAIProvider


def make_llm_provider(settings: Settings) -> LLMProvider:
    """Return the LLM provider named in settings.

    Args:
        settings: Application settings including provider and credentials.

    Returns:
        OpenAI (optionally wrapped with Groq fallback) or Groq alone.

    Raises:
        ValueError: If the provider name is not supported.
    """
    if settings.llm_provider == "openai":
        primary = OpenAIProvider(
            settings.openai_api_key,
            settings.openai_model,
            settings.llm_timeout_s,
            pricing=settings.model_pricing.get(settings.openai_model),
        )
        if settings.groq_api_key:
            fallback = GroqProvider(
                settings.groq_api_key,
                settings.groq_model,
                settings.llm_timeout_s,
                pricing=settings.model_pricing.get(settings.groq_model),
            )
            return FallbackProvider(primary, fallback)
        return primary
    elif settings.llm_provider == "groq":
        return GroqProvider(
            settings.groq_api_key,
            settings.groq_model,
            settings.llm_timeout_s,
            pricing=settings.model_pricing.get(settings.groq_model),
        )
    raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")


def get_llm() -> LLMProvider:
    """Return the process LLM provider for FastAPI `Depends`."""
    return make_llm_provider(get_settings())
