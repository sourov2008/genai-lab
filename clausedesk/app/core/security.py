"""Authentication helpers used by FastAPI dependencies."""

from __future__ import annotations


async def get_current_user_id() -> int:
    """Return the authenticated user id.

    Mock implementation until JWT auth is added.

    Returns:
        Hardcoded seed user id `1`.
    """
    return 1
