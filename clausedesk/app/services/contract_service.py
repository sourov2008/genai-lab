"""Contract persistence service functions."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Contract
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


async def get_contracts(db: AsyncSession, user_id: int) -> list[Contract]:
    """Return all contracts for a user, newest first.

    Args:
        db: Active async database session.
        user_id: Owner whose contracts are listed.

    Returns:
        Matching `Contract` rows ordered by `created_at` descending.
    """
    result = await db.execute(
        select(Contract)
        .where(Contract.user_id == user_id)
        .order_by(Contract.created_at.desc())
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
        select(Contract).where(
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

