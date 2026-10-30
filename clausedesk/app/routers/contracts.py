from __future__ import annotations

from fastapi import APIRouter, Depends, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user_id
from app.db.session import get_db
from app.schemas.contract import ContractDetailResponse, ContractUploadResponse
from app.services import contract_service

router = APIRouter(prefix="/contracts", tags=["contracts"])


@router.post("/", response_model=ContractUploadResponse)
async def upload_contract(
    filename: str = Form(...),
    raw_text: str = Form(...),
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> ContractUploadResponse:
    contract = await contract_service.create_contract(
        db,
        user_id=user_id,
        filename=filename,
        raw_text=raw_text,
    )
    return ContractUploadResponse.model_validate(contract)


@router.get("/", response_model=list[ContractUploadResponse])
async def list_contracts(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> list[ContractUploadResponse]:
    contracts = await contract_service.get_contracts(db, user_id=user_id)
    return [ContractUploadResponse.model_validate(c) for c in contracts]
