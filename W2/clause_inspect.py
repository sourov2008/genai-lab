#!/usr/bin/env python3
"""Inspect a clause file: character/word counts, token estimate, and gpt-4o-mini cost."""

from __future__ import annotations

import argparse
from pathlib import Path

INPUT_USD_PER_MILLION = 0.15
OUTPUT_USD_PER_MILLION = 0.60
ASSUMED_OUTPUT_TOKENS = 500
CHARS_PER_TOKEN = 4
CONTEXT_CHARS = 50

DOUBLE = "═" * 52
SINGLE = "─" * 52


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect a text file and estimate gpt-4o-mini extraction cost.",
    )
    parser.add_argument("filepath", type=Path, help="Path to the clause/text file")
    parser.add_argument(
        "--keyword",
        help="Search the text case-insensitively and print line + context",
    )
    return parser.parse_args()


def load_text(path: Path) -> str:
    if not path.is_file():
        raise SystemExit(f"error: file not found: {path}")
    return path.read_text(encoding="utf-8")


def inspect(text: str) -> dict[str, float | int]:
    chars = len(text)
    words = len(text.split())
    try:
        if chars == 0 or words == 0:
            raise ZeroDivisionError("empty file")
        est_tokens = chars / CHARS_PER_TOKEN
        input_cost = (est_tokens / 1_000_000) * INPUT_USD_PER_MILLION
    except ZeroDivisionError:
        est_tokens = 0.0
        input_cost = 0.0
    output_cost = (ASSUMED_OUTPUT_TOKENS / 1_000_000) * OUTPUT_USD_PER_MILLION
    return {
        "chars": chars,
        "words": words,
        "est_tokens": est_tokens,
        "input_cost": input_cost,
        "output_cost": output_cost,
        "total_cost": input_cost + output_cost,
        "empty": int(chars == 0 or words == 0),
    }


def find_keyword_matches(text: str, keyword: str) -> list[tuple[int, str]]:
    needle = keyword.lower()
    matches: list[tuple[int, str]] = []
    if not needle:
        return matches

    for line_no, line in enumerate(text.splitlines(), start=1):
        haystack = line.lower()
        start_at = 0
        while True:
            idx = haystack.find(needle, start_at)
            if idx == -1:
                break
            left = max(0, idx - CONTEXT_CHARS)
            right = min(len(line), idx + len(keyword) + CONTEXT_CHARS)
            snippet = line[left:right].replace("\t", " ")
            prefix = "…" if left > 0 else ""
            suffix = "…" if right < len(line) else ""
            matches.append((line_no, f"{prefix}{snippet}{suffix}"))
            start_at = idx + max(len(keyword), 1)
    return matches


def fmt_int(n: int) -> str:
    return f"{n:,}"


def fmt_num(n: float) -> str:
    return f"{n:,.1f}"


def fmt_usd(n: float) -> str:
    return f"${n:.6f}"


def print_report(
    path: Path,
    stats: dict[str, float | int],
    keyword: str | None = None,
    matches: list[tuple[int, str]] | None = None,
) -> None:
    print(DOUBLE)
    print("  Clause Inspector")
    print(DOUBLE)
    print(f"  File              {path}")
    print(f"  Characters        {fmt_int(int(stats['chars']))}")
    print(f"  Words             {fmt_int(int(stats['words']))}")
    if stats["empty"]:
        print("  Est. tokens       0.0  (empty file — ZeroDivisionError handled)")
    else:
        print(f"  Est. tokens       {fmt_num(float(stats['est_tokens']))}  (chars ÷ {CHARS_PER_TOKEN})")
    print(SINGLE)
    print("  gpt-4o-mini extraction")
    print(f"  Input  ${INPUT_USD_PER_MILLION:.2f}/1M   {fmt_usd(float(stats['input_cost']))}")
    print(
        f"  Output ${OUTPUT_USD_PER_MILLION:.2f}/1M   {fmt_usd(float(stats['output_cost']))}"
        f"  ({ASSUMED_OUTPUT_TOKENS} tokens)"
    )
    print(f"  Total             {fmt_usd(float(stats['total_cost']))}")

    if keyword is not None:
        print(SINGLE)
        print(f"  Keyword search    {keyword!r}  (case-insensitive)")
        if not matches:
            print("  Matches           0")
        else:
            print(f"  Matches           {len(matches)}")
            for line_no, snippet in matches:
                print(f"  L{line_no:<6}          {snippet}")

    print(DOUBLE)


def main() -> None:
    args = parse_args()
    text = load_text(args.filepath)
    stats = inspect(text)
    matches = find_keyword_matches(text, args.keyword) if args.keyword else None
    print_report(args.filepath, stats, keyword=args.keyword, matches=matches)


if __name__ == "__main__":
    main()
