"""Contract persistence service functions."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Clause, Contract
from app.models.clause import ClauseStatus
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


async def update_clause_status(
    db: AsyncSession,
    clause_id: int,
    user_id: int,
    new_status: str,
) -> Clause | None:
    """Update a clause review status if the user owns the parent contract.

    Args:
        db: Active async database session.
        clause_id: Primary key of the clause.
        user_id: Owner that must match the parent contract.
        new_status: Replacement `ClauseStatus` value.

    Returns:
        The refreshed `Clause`, or `None` if missing or not owned.
    """
    result = await db.execute(
        select(Clause)
        .join(Contract, Clause.contract_id == Contract.id)
        .where(
            Clause.id == clause_id,
            Contract.user_id == user_id,
        )
    )
    clause = result.scalar_one_or_none()
    if clause is None:
        return None
    clause.status = new_status  # values from ClauseStatus (review, verified, ...)
    await db.commit()
    await db.refresh(clause)
    return clause


async def search_clauses_by_vector(
    db: AsyncSession,
    query_vector: list[float],
    limit: int = 5,
) -> list[Clause]:
    """Return clauses nearest to `query_vector` by cosine distance.

    Rows with a NULL embedding are excluded so they are not ranked.

    Args:
        db: Active async database session.
        query_vector: Query embedding (1536 dimensions).
        limit: Maximum number of clauses to return.

    Returns:
        Clauses ordered from nearest to farthest.
    """
    result = await db.execute(
        select(Clause)
        .where(Clause.embedding.is_not(None))
        .order_by(Clause.embedding.cosine_distance(query_vector))
        .limit(limit)
    )
    return list(result.scalars().all())
