"""Summarize `evals/evaluation_results.csv` into a Markdown comparison table."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

INPUT_PRICE_PER_1M = 0.15
OUTPUT_PRICE_PER_1M = 0.60

_ROOT = Path(__file__).resolve().parents[1]
_EVALS_DIR = _ROOT / "evals"
_CSV_PATH = _EVALS_DIR / "evaluation_results.csv"
_MD_PATH = _EVALS_DIR / "evaluation_comparison_table.md"


def _is_valid_json(value: str) -> bool:
    """Return True when a CSV `valid_json` cell is a truthy flag.

    Args:
        value: Raw CSV cell.

    Returns:
        True for `true` / `TRUE` / `1`.
    """
    return value.strip().lower() in {"true", "1", "yes"}


def _row_cost(in_tokens: float, out_tokens: float) -> float:
    """Return USD cost for one completion using gpt-4o-mini list prices.

    Args:
        in_tokens: Prompt token count.
        out_tokens: Completion token count.

    Returns:
        Estimated cost in USD.
    """
    return (in_tokens / 1_000_000 * INPUT_PRICE_PER_1M) + (
        out_tokens / 1_000_000 * OUTPUT_PRICE_PER_1M
    )


def _group_rows(
    rows: list[dict[str, str]],
) -> dict[tuple[float, int], list[dict[str, str]]]:
    """Bucket evaluation rows by temperature and max_tokens, attaching per-row cost.

    Args:
        rows: DictWriter rows from `evals/evaluation_results.csv`.

    Returns:
        Mapping of `(temperature, max_tokens)` to matching rows.
    """
    groups: dict[tuple[float, int], list[dict[str, str]]] = defaultdict(list)
    cost_totals: dict[tuple[float, int], float] = defaultdict(float)
    for row in rows:
        key = (float(row["temperature"]), int(row["max_tokens"]))
        in_tokens = float(row["in_tokens"])
        out_tokens = float(row["out_tokens"])
        cost = _row_cost(in_tokens, out_tokens)
        cost_totals[key] += cost
        row["_cost"] = str(cost)
        groups[key].append(row)
    for key, group in groups.items():
        for row in group:
            row["_group_cost_total"] = str(cost_totals[key])
    return groups


def _summarize(
    rows: list[dict[str, str]],
) -> tuple[float, float, float, float, float]:
    """Compute latency, token, validity, and 1K-request cost stats.

    Args:
        rows: Rows that share one hyperparameter pair.

    Returns:
        `(avg_latency_s, avg_in_tokens, avg_out_tokens, validity_pct,
        est_cost_per_1k)`.
    """
    n = len(rows)
    avg_latency_s = sum(float(r["latency_ms"]) for r in rows) / n / 1000
    avg_in = sum(float(r["in_tokens"]) for r in rows) / n
    avg_out = sum(float(r["out_tokens"]) for r in rows) / n
    valid = sum(1 for r in rows if _is_valid_json(r["valid_json"]))
    validity_pct = 100.0 * valid / n
    total_cost = sum(float(r["_cost"]) for r in rows)
    est_cost_per_1k = (total_cost / n) * 1000
    return avg_latency_s, avg_in, avg_out, validity_pct, est_cost_per_1k


def build_markdown(groups: dict[tuple[float, int], list[dict[str, str]]]) -> str:
    """Render the comparison table.

    Args:
        groups: Evaluation rows keyed by `(temperature, max_tokens)`.

    Returns:
        Markdown document with title and table.
    """
    lines = [
        "# Production Hyperparameter Evaluation",
        "",
        "| Temperature | Max Tokens | Avg Latency (s) | Avg In Tokens | Avg Out Tokens | JSON Validity | Est. Cost / 1K Requests |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for temp, max_tok in sorted(groups):
        avg_latency_s, avg_in, avg_out, validity_pct, est_cost_per_1k = _summarize(
            groups[(temp, max_tok)]
        )
        lines.append(
            f"| {temp:.1f} | {max_tok} | {avg_latency_s:.2f} | "
            f"{avg_in:.1f} | {avg_out:.1f} | {validity_pct:.0f}% | "
            f"${est_cost_per_1k:.4f} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    """Read the evaluation CSV, print the table, and write `evals/evaluation_comparison_table.md`."""
    Path("evals").mkdir(exist_ok=True)
    _EVALS_DIR.mkdir(exist_ok=True)
    with _CSV_PATH.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    markdown = build_markdown(_group_rows(rows))
    print(markdown)
    _MD_PATH.write_text(markdown, encoding="utf-8")


if __name__ == "__main__":
    main()
