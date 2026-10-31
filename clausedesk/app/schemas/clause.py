"""Pydantic schemas for extracted clauses."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ClauseBase(BaseModel):
    """Shared clause fields for create and response payloads."""

    clause_type: str
    quote: str
    char_start: int | None = None
    char_end: int | None = None
    page_number: int | None = None
    confidence: float | None = None
    verified: bool = False
    status: str = "review"


class ClauseResponse(ClauseBase):
    """Clause as returned by the API, including persistence ids."""

    id: int
    prompt_run_id: int | None

    model_config = ConfigDict(from_attributes=True)
