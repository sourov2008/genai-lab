"""Retry helper for LLM provider calls."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")


async def with_retry(operation: Callable[[], Awaitable[T]]) -> T:
    """Await `operation()` once.

    A later revision can add backoff for rate limits and 5xx errors.

    Args:
        operation: Zero-arg callable that returns an awaitable.

    Returns:
        The awaited result of `operation()`.
    """
    return await operation()
