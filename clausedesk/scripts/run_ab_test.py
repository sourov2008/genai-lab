"""Run extraction prompts v1 and v2 against the golden set."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings
from app.llm.base import LLMRequest, Message
from app.llm.factory import make_llm_provider
from app.llm.prompt_loader import load_prompt

_ROOT = Path(__file__).resolve().parents[1]
_GOLDEN_SET = _ROOT / "data" / "golden_set.json"


async def evaluate(prompt_version: str, cases: list[dict]) -> None:
    """Call the LLM once per golden case and print expected vs raw output.

    Args:
        prompt_version: Prompt suffix such as `v1` or `v2`.
        cases: Golden-set objects with `id`, `text`, and `expected_clause_types`.
    """
    system_prompt = load_prompt(prompt_version)
    settings = get_settings()
    llm = make_llm_provider(settings)
    for case in cases:
        request = LLMRequest(
            messages=[
                Message(role="system", content=system_prompt),
                Message(role="user", content=case["text"]),
            ],
            response_format={"type": "json_object"},
        )
        response = await llm.complete(request)
        print(
            f"[v{prompt_version}] Case {case['id']}: "
            f"expected={case['expected_clause_types']}, got={response.text}"
        )


async def main() -> None:
    """Load the golden set and evaluate prompt v1 then v2."""
    cases = json.loads(_GOLDEN_SET.read_text(encoding="utf-8"))
    await evaluate("v1", cases)
    await evaluate("v2", cases)


if __name__ == "__main__":
    asyncio.run(main())
