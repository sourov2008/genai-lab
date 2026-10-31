"""Clause ORM model and review status values."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.contract import Contract
    from app.models.prompt_run import PromptRun


class ClauseStatus(str, Enum):
    """Review state of an extracted clause."""

    AUTO_ACCEPTED = "auto_accepted"
    REVIEW = "review"
    VERIFIED = "verified"
    REJECTED = "rejected"


class Clause(Base):
    """Quoted clause extracted from a contract."""

    __tablename__ = "clauses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    contract_id: Mapped[int] = mapped_column(
        ForeignKey("contracts.id"), index=True, nullable=False
    )
    clause_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    quote: Mapped[str] = mapped_column(Text, nullable=False)
    char_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    char_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default=ClauseStatus.REVIEW.value, nullable=False
    )
    prompt_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("prompt_runs.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    contract: Mapped[Contract] = relationship(back_populates="clauses")
    prompt_run: Mapped[PromptRun | None] = relationship()
