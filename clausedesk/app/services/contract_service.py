"""Contract persistence service functions."""

from __future__ import annotations

import json

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.llm.base import LLMProvider, LLMRequest, Message
from app.llm.errors import LLMBadRequestError
from app.models import Contract, PromptRun
from app.models.clause import Clause, ClauseStatus
from app.models.contract import ContractStatus

async def create_contract(
    db: AsyncSession,
    user_id: int,
    filename: str,
    raw_text: str,
) -> Contract:
    """Create and persist a new contract in pending status.

    Args:
        db: Active async database session.
        user_id: Owner of the contract.
        filename: Original file name.
        raw_text: Full contract text.

    Returns:
        The saved `Contract` with a database-assigned id.
    """
    contract = Contract(
        user_id=user_id,
        filename=filename,
        raw_text=raw_text,
        status=ContractStatus.PENDING.value,
    )
    db.add(contract)
    await db.commit()
    await db.refresh(contract)
    return contract


async def get_contracts_count(
    db: AsyncSession,
    user_id: int,
    status: str | None = None,
) -> int:
    """Return how many contracts the user has, optionally filtered by status.

    Args:
        db: Active async database session.
        user_id: Owner whose contracts are counted.
        status: Optional status filter.

    Returns:
        Matching row count.
    """
    query = select(func.count(Contract.id)).where(Contract.user_id == user_id)
    if status is not None:
        query = query.where(Contract.status == status)
    result = await db.execute(query)
    return int(result.scalar_one())


async def get_contracts(
    db: AsyncSession,
    user_id: int,
    limit: int = 10,
    offset: int = 0,
    status: str | None = None,
) -> list[Contract]:
    """Return a page of contracts for a user, newest first.

    Args:
        db: Active async database session.
        user_id: Owner whose contracts are listed.
        limit: Maximum rows to return.
        offset: Number of rows to skip.
        status: Optional status filter.

    Returns:
        Matching `Contract` rows ordered by `created_at` descending.
    """
    query = select(Contract).where(Contract.user_id == user_id)
    if status is not None:
        query = query.where(Contract.status == status)
    result = await db.execute(
        query.order_by(Contract.created_at.desc()).limit(limit).offset(offset)
    )
    return list(result.scalars().all())



async def get_contract_by_id(
    db: AsyncSession,
    contract_id: int,
    user_id: int,
) -> Contract | None:
    """Return a contract owned by the user, or None if missing.

    Args:
        db: Active async database session.
        contract_id: Primary key of the contract.
        user_id: Owner that must match the row.

    Returns:
        The `Contract` if `id` and `user_id` match, otherwise `None`.
    """
    result = await db.execute(
        select(Contract)
        .options(selectinload(Contract.clauses))
        .where(
            Contract.id == contract_id,
            Contract.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def delete_contract(
    db: AsyncSession,
    contract_id: int,
    user_id: int,
) -> bool:
    """Delete a contract if it exists and belongs to the user.

    Args:
        db: Active async database session.
        contract_id: Primary key of the contract.
        user_id: Owner that must match the row.

    Returns:
        `True` if a row was deleted, otherwise `False`.
    """
    contract = await get_contract_by_id(db, contract_id, user_id)
    if contract is None:
        return False
    await db.delete(contract)
    await db.commit()
    return True


async def update_contract(
    db: AsyncSession,
    contract: Contract,
    filename: str | None = None,
    raw_text: str | None = None,
    status: str | None = None,
) -> Contract:
    """Apply non-None fields to a contract and persist the change.

    Args:
        db: Active async database session.
        contract: Loaded contract instance to update.
        filename: Replacement file name, if provided.
        raw_text: Replacement contract text, if provided.
        status: Replacement processing status, if provided.

    Returns:
        The refreshed `Contract`.

    Raises:
        IntegrityError: If commit violates a uniqueness constraint on filename.
    """
    if filename is not None:
        contract.filename = filename
    if raw_text is not None:
        contract.raw_text = raw_text
    if status is not None:
        contract.status = status
    await db.commit()
    await db.refresh(contract)
    result = await db.execute(
        select(Contract)
        .options(selectinload(Contract.clauses))
        .where(Contract.id == contract.id)
    )
    return result.scalar_one()


async def extract_clauses(
    db: AsyncSession,
    contract: Contract,
    llm: LLMProvider,
) -> Contract:
    """Call the LLM, persist extracted clauses, and verify quotes.

    Args:
        db: Active async database session.
        contract: Contract whose `raw_text` is sent to the LLM.
        llm: Provider used for completion (must be faked in tests).

    Returns:
        The contract reloaded with clauses.
    """
    response = await llm.complete(
        LLMRequest(
            messages=[
                Message(
                    role="system",
                    content=(
                        "You are a legal contract analyzer. Extract the "
                        "termination clause. Return a JSON object with a "
                        "'clauses' array. Each clause must have 'clause_type' "
                        "(string), 'quote' (exact substring from text), and "
                        "'confidence' (float). If none, return {\"clauses\": []}."
                    ),
                ),
                Message(role="user", content=contract.raw_text),
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
        )
    )
    prompt_run = PromptRun(
        contract_id=contract.id,
        provider=response.provider,
        model=response.model,
        raw_response=response.text,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
        cost_usd=response.usage.cost_usd,
        latency_ms=response.latency_ms,
        request_id=response.request_id,
    )
    db.add(prompt_run)
    await db.flush()
    text = response.text.strip()
    if text.startswith("```json"):
        text = text.removeprefix("```json").strip()
        if text.endswith("```"):
            text = text.removesuffix("```").strip()
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise LLMBadRequestError("LLM returned invalid JSON") from exc
    for item in payload.get("clauses", []):
        quote = item["quote"]
        verified = quote in contract.raw_text
        confidence = item.get("confidence", 0.0) or 0.0
        status = (
            ClauseStatus.AUTO_ACCEPTED.value
            if (verified and confidence >= 0.7)
            else ClauseStatus.REVIEW.value
        )
        db.add(
            Clause(
                contract_id=contract.id,
                clause_type=item["clause_type"],
                quote=quote,
                confidence=confidence,
                verified=verified,
                status=status,
                prompt_run_id=prompt_run.id,
            )
        )
    contract.status = ContractStatus.READY.value
    await db.commit()
    db.expire(contract, ["clauses"])
    loaded = await get_contract_by_id(db, contract.id, contract.user_id)
    if loaded is None:
        return contract
    return loaded



