"""Compare OpenAI and Groq on the golden set at production extraction defaults."""

from __future__ import annotations

import asyncio
import csv
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import Settings, get_settings
from app.llm.base import LLMRequest, Message
from app.llm.factory import make_llm_provider
from app.llm.prompt_loader import load_prompt

_ROOT = Path(__file__).resolve().parents[1]
_GOLDEN_SET = _ROOT / "data" / "golden_set.json"
_EVALS_DIR = _ROOT / "evals"
_RESULTS_CSV = _EVALS_DIR / "provider_comparison.csv"
_FIELDNAMES = [
    "provider",
    "case_id",
    "latency_ms",
    "in_tokens",
    "out_tokens",
    "valid_json",
    "error_msg",
]


async def run_provider(provider_name: str, cases: list[dict]) -> list[dict]:
    """Run every golden case on one LLM provider at locked extraction defaults.

    Args:
        provider_name: `openai` or `groq`.
        cases: Golden-set objects with `id` and `text`.

    Returns:
        One result dict per case (latency, tokens, JSON validity, error_msg).
    """
    settings: Settings = get_settings().model_copy(
        update={"llm_provider": provider_name}
    )
    llm = make_llm_provider(settings)
    system_prompt = load_prompt(settings.prompt_version)
    results: list[dict] = []
    for case in cases:
        started = time.monotonic()
        is_valid = False
        in_tokens = 0
        out_tokens = 0
        error_msg = ""
        try:
            response = await llm.complete(
                LLMRequest(
                    messages=[
                        Message(role="system", content=system_prompt),
                        Message(role="user", content=case["text"]),
                    ],
                    temperature=0.0,
                    max_tokens=1024,
                    response_format={"type": "json_object"},
                )
            )
            in_tokens = response.usage.input_tokens
            out_tokens = response.usage.output_tokens
            try:
                json.loads(response.text)
                is_valid = True
            except json.JSONDecodeError:
                is_valid = False
        except Exception as exc:
            is_valid = False
            error_msg = str(exc)
            print(
                f"{provider_name} case {case['id']} failed: {error_msg}"
            )
        latency_ms = int((time.monotonic() - started) * 1000)
        results.append(
            {
                "provider": provider_name,
                "case_id": case["id"],
                "latency_ms": latency_ms,
                "in_tokens": in_tokens,
                "out_tokens": out_tokens,
                "valid_json": is_valid,
                "error_msg": error_msg,
            }
        )
    return results


async def main() -> None:
    """Compare OpenAI then Groq and write `evals/provider_comparison.csv`."""
    cases = json.loads(_GOLDEN_SET.read_text(encoding="utf-8"))
    combined: list[dict] = []
    combined.extend(await run_provider("openai", cases))
    combined.extend(await run_provider("groq", cases))
    Path("evals").mkdir(exist_ok=True)
    _EVALS_DIR.mkdir(exist_ok=True)
    with _RESULTS_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=_FIELDNAMES)
        writer.writeheader()
        writer.writerows(combined)
    print(f"Wrote evaluation results to {_RESULTS_CSV}")


if __name__ == "__main__":
    asyncio.run(main())
