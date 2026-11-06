"""Unit tests for `make_llm_provider` provider selection."""

from __future__ import annotations

from app.core.config import get_settings
from app.llm.factory import make_llm_provider
from app.llm.groq_provider import GroqProvider
from app.llm.openai_provider import OpenAIProvider


def test_make_llm_provider_openai() -> None:
    """Select OpenAI when `llm_provider` is `openai` and Groq is unset."""
    settings = get_settings()
    original_provider = settings.llm_provider
    original_groq_key = settings.groq_api_key
    try:
        settings.llm_provider = "openai"
        settings.groq_api_key = ""
        provider = make_llm_provider(settings)
        assert isinstance(provider, OpenAIProvider)
    finally:
        settings.llm_provider = original_provider
        settings.groq_api_key = original_groq_key


def test_make_llm_provider_groq() -> None:
    """Select Groq when `llm_provider` is `groq`."""
    settings = get_settings()
    original = settings.llm_provider
    try:
        settings.llm_provider = "groq"
        provider = make_llm_provider(settings)
        assert isinstance(provider, GroqProvider)
    finally:
        settings.llm_provider = original
