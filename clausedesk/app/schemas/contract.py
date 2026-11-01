"""Pydantic schemas for contract upload and detail responses."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.clause import ClauseResponse


class ContractUploadResponse(BaseModel):
    """Minimal contract payload after upload or list."""

    id: int
    filename: str
    status: str

    model_config = ConfigDict(from_attributes=True)


class ContractDetailResponse(BaseModel):
    """Full contract payload including source text and clauses."""

    id: int
    filename: str
    status: str
    raw_text: str
    clauses: list[ClauseResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ContractUpdate(BaseModel):
    """Partial contract fields for PATCH-style updates."""

    filename: str | None = None
    raw_text: str | None = None
    status: str | None = None


class PaginatedContractResponse(BaseModel):
    """Paginated list of contract summaries."""

    total: int
    limit: int
    offset: int
    items: list[ContractUploadResponse]
