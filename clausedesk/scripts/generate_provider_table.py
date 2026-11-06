"""Summarize `evals/provider_comparison.csv` into a Markdown table."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_EVALS_DIR = _ROOT / "evals"
_CSV_PATH = _EVALS_DIR / "provider_comparison.csv"
_MD_PATH = _EVALS_DIR / "provider_comparison_table.md"


def _is_valid_json(value: str) -> bool:
    """Return True when a CSV `valid_json` cell is a truthy flag.

    Args:
        value: Raw CSV cell.

    Returns:
        True for `true` / `TRUE` / `1`.
    """
    return value.strip().lower() in {"true", "1", "yes"}


def _summarize(rows: list[dict[str, str]]) -> tuple[float, float, float]:
    """Compute mean latency, mean out tokens, and JSON validity rate.

    Args:
        rows: Rows for a single provider.

    Returns:
        `(avg_latency_ms, avg_out_tokens, validity_pct)`.
    """
    n = len(rows)
    avg_latency_ms = sum(float(r["latency_ms"]) for r in rows) / n
    avg_out = sum(float(r["out_tokens"]) for r in rows) / n
    valid = sum(1 for r in rows if _is_valid_json(r["valid_json"]))
    validity_pct = 100.0 * valid / n
    return avg_latency_ms, avg_out, validity_pct


def build_markdown(groups: dict[str, list[dict[str, str]]]) -> str:
    """Render the provider comparison table.

    Args:
        groups: Rows keyed by provider name.

    Returns:
        Markdown document with title and table.
    """
    lines = [
        "# Provider Comparison",
        "",
        "| Provider | Avg Latency (ms) | Avg Out Tokens | JSON Validity |",
        "| :--- | ---: | ---: | ---: |",
    ]
    for provider in sorted(groups):
        avg_latency_ms, avg_out, validity_pct = _summarize(groups[provider])
        lines.append(
            f"| {provider} | {avg_latency_ms:.0f} | {avg_out:.1f} | "
            f"{validity_pct:.0f}% |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    """Read the provider CSV, print the table, and write `evals/provider_comparison_table.md`."""
    Path("evals").mkdir(exist_ok=True)
    _EVALS_DIR.mkdir(exist_ok=True)
    with _CSV_PATH.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[row["provider"]].append(row)
    markdown = build_markdown(groups)
    print(markdown)
    _MD_PATH.write_text(markdown, encoding="utf-8")


if __name__ == "__main__":
    main()
