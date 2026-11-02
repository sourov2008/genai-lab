"""Smoke-test the configured LLM provider."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings
from app.llm.base import LLMRequest, Message
from app.llm.factory import make_llm_provider


async def main() -> None:
    """Send one completion and print text, tokens, and latency."""
    settings = get_settings()
    provider = make_llm_provider(settings)
    req = LLMRequest(
        messages=[
            Message(role="user", content="Say 'Hello from OpenAI'"),
        ]
    )
    response = await provider.complete(req)
    print(response.text)
    print(
        f"tokens in={response.usage.input_tokens} "
        f"out={response.usage.output_tokens}"
    )
    print(f"latency_ms={response.latency_ms}")


if __name__ == "__main__":
    asyncio.run(main())
