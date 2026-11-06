"""Evaluate temperature and max_tokens against the golden extraction set."""

from __future__ import annotations

import asyncio
import csv
import itertools
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings
from app.llm.base import LLMRequest, Message
from app.llm.factory import make_llm_provider
from app.llm.prompt_loader import load_prompt

_ROOT = Path(__file__).resolve().parents[1]
_GOLDEN_SET = _ROOT / "data" / "golden_set.json"
_EVALS_DIR = _ROOT / "evals"
_RESULTS_CSV = _EVALS_DIR / "evaluation_results.csv"
_FIELDNAMES = [
    "case_id",
    "temperature",
    "max_tokens",
    "latency_ms",
    "in_tokens",
    "out_tokens",
    "valid_json",
    "error",
]


async def run_sweep() -> None:
    """Run every temperature × max_tokens combo on each golden case.

    Writes `evals/evaluation_results.csv` with latency, token usage, and JSON validity.
    """
    cases = json.loads(_GOLDEN_SET.read_text(encoding="utf-8"))
    settings = get_settings()
    llm = make_llm_provider(settings)
    system_prompt = load_prompt(settings.prompt_version)
    temperatures = [0.0, 0.3, 0.7]
    max_tokens_list = [256, 1024]
    results: list[dict] = []

    for temp, max_tok in itertools.product(temperatures, max_tokens_list):
        for case in cases:
            started = time.monotonic()
            is_valid = False
            error_message = ""
            in_tokens = 0
            out_tokens = 0
            try:
                response = await llm.complete(
                    LLMRequest(
                        messages=[
                            Message(role="system", content=system_prompt),
                            Message(role="user", content=case["text"]),
                        ],
                        temperature=temp,
                        max_tokens=max_tok,
                        response_format={"type": "json_object"},
                    )
                )
                in_tokens = response.usage.input_tokens
                out_tokens = response.usage.output_tokens
                try:
                    json.loads(response.text)
                    is_valid = True
                except json.JSONDecodeError as exc:
                    error_message = str(exc)
            except Exception as exc:
                error_message = str(exc)
            latency_ms = int((time.monotonic() - started) * 1000)
            results.append(
                {
                    "case_id": case["id"],
                    "temperature": temp,
                    "max_tokens": max_tok,
                    "latency_ms": latency_ms,
                    "in_tokens": in_tokens,
                    "out_tokens": out_tokens,
                    "valid_json": is_valid,
                    "error": error_message,
                }
            )

    Path("evals").mkdir(exist_ok=True)
    _EVALS_DIR.mkdir(exist_ok=True)
    with _RESULTS_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=_FIELDNAMES)
        writer.writeheader()
        writer.writerows(results)
    print(f"Wrote evaluation results to {_RESULTS_CSV}")


if __name__ == "__main__":
    asyncio.run(run_sweep())
