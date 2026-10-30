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
    result = await db.execute(
        select(Contract)
        .where(Contract.user_id == user_id)
        .order_by(Contract.created_at.desc())
    )
    return list(result.scalars().all())
