"""JSON schema for LLM clause extraction output."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ExtractedClause(BaseModel):
    """One clause object expected from the extraction prompt."""

    model_config = ConfigDict(extra="forbid")

    clause_type: str
    quote: str
    confidence: float


class ExtractionResult(BaseModel):
    """Top-level LLM JSON payload: a list of extracted clauses."""

    model_config = ConfigDict(extra="forbid")

    clauses: list[ExtractedClause]
