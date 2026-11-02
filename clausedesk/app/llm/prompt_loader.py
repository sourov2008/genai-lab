"""Load versioned extraction prompts from the repo `prompts/` directory."""

from __future__ import annotations

from pathlib import Path


def load_prompt(version: str) -> str:
    """Return the extraction prompt file for a version tag.

    Args:
        version: Prompt suffix, for example `v1` or `v2` (`extract_{version}.md`).

    Returns:
        File contents with leading and trailing whitespace removed.

    Raises:
        FileNotFoundError: If `prompts/extract_{version}.md` does not exist.
    """
    path = Path(__file__).resolve().parents[2] / "prompts" / f"extract_{version}.md"
    if not path.exists():
        raise FileNotFoundError(path)
    return path.read_text(encoding="utf-8").strip()
