# src/llm/factory.py
from ..config import Settings
from .base import LLMProvider
from .gemini import GeminiProvider
from .groq import GroqProvider


def make_llm_provider(settings: Settings) -> LLMProvider:
    p = settings.llm_provider.lower()

    if p == "gemini":
        return GeminiProvider(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
            pricing=settings.model_pricing.get(settings.gemini_model),
            timeout_s=settings.llm_timeout_s,
        )

    if p == "groq":
        return GroqProvider(
            api_key=settings.groq_api_key,
            model=settings.groq_model,
            pricing=settings.model_pricing.get(settings.groq_model),
            timeout_s=settings.llm_timeout_s,
        )

    raise ValueError(f"Unknown LLM_PROVIDER: {p}")
