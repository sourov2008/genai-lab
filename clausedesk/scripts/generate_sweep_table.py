"""Summarize `data/sweep_results.csv` into a Markdown comparison table."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_CSV_PATH = _ROOT / "data" / "sweep_results.csv"
_MD_PATH = _ROOT / "docs" / "sweep_comparison_table.md"


def _is_valid_json(value: str) -> bool:
    """Return True when a CSV `valid_json` cell is a truthy flag.

    Args:
        value: Raw CSV cell.

    Returns:
        True for `true` / `TRUE` / `1`.
    """
    return value.strip().lower() in {"true", "1", "yes"}


def _group_rows(rows: list[dict[str, str]]) -> dict[tuple[float, int], list[dict[str, str]]]:
    """Bucket sweep rows by temperature and max_tokens.

    Args:
        rows: DictWriter rows from `sweep_results.csv`.

    Returns:
        Mapping of `(temperature, max_tokens)` to matching rows.
    """
    groups: dict[tuple[float, int], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        key = (float(row["temperature"]), int(row["max_tokens"]))
        groups[key].append(row)
    return groups


def _summarize(rows: list[dict[str, str]]) -> tuple[float, float, float]:
    """Compute mean latency (s), mean out tokens, and JSON validity rate.

    Args:
        rows: Rows that share one hyperparameter pair.

    Returns:
        `(avg_latency_s, avg_out_tokens, validity_pct)`.
    """
    n = len(rows)
    avg_latency_s = sum(float(r["latency_ms"]) for r in rows) / n / 1000
    avg_out = sum(float(r["out_tokens"]) for r in rows) / n
    valid = sum(1 for r in rows if _is_valid_json(r["valid_json"]))
    validity_pct = 100.0 * valid / n
    return avg_latency_s, avg_out, validity_pct


def build_markdown(groups: dict[tuple[float, int], list[dict[str, str]]]) -> str:
    """Render the comparison table.

    Args:
        groups: Sweep rows keyed by `(temperature, max_tokens)`.

    Returns:
        Markdown document with title and table.
    """
    lines = [
        "# Production Hyperparameter Comparison",
        "",
        "| Temperature | Max Tokens | Avg Latency (s) | Avg Out Tokens | JSON Validity |",
        "| ---: | ---: | ---: | ---: | ---: |",
    ]
    for temp, max_tok in sorted(groups):
        avg_latency_s, avg_out, validity_pct = _summarize(groups[(temp, max_tok)])
        lines.append(
            f"| {temp:.1f} | {max_tok} | {avg_latency_s:.2f} | "
            f"{avg_out:.1f} | {validity_pct:.0f}% |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    """Read the sweep CSV, print the table, and write `docs/sweep_comparison_table.md`."""
    with _CSV_PATH.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    markdown = build_markdown(_group_rows(rows))
    print(markdown)
    _MD_PATH.parent.mkdir(parents=True, exist_ok=True)
    _MD_PATH.write_text(markdown, encoding="utf-8")


if __name__ == "__main__":
    main()
