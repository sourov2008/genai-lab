"""HTTP routes for uploading and listing contracts."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Response
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
    """Create a contract from multipart form fields.

    Args:
        filename: Original file name.
        raw_text: Full contract text.
        db: Request-scoped database session.
        user_id: Authenticated user id.

    Returns:
        The created contract summary.
    """
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
    """List contracts owned by the current user.

    Args:
        db: Request-scoped database session.
        user_id: Authenticated user id.

    Returns:
        Contract summaries ordered by the service layer.
    """
    contracts = await contract_service.get_contracts(db, user_id=user_id)
    return [ContractUploadResponse.model_validate(c) for c in contracts]


@router.get("/{contract_id}", response_model=ContractDetailResponse)
async def get_contract(
    contract_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> ContractDetailResponse:
    """Return one contract owned by the current user.

    Args:
        contract_id: Contract primary key.
        db: Request-scoped database session.
        user_id: Authenticated user id.

    Returns:
        Contract detail including source text and clauses.

    Raises:
        HTTPException: 404 if the contract is missing or not owned by the user.
    """
    contract = await contract_service.get_contract_by_id(db, contract_id, user_id)
    if contract is None:
        raise HTTPException(status_code=404, detail="Contract not found")
    return ContractDetailResponse.model_validate(contract)


@router.delete("/{contract_id}", status_code=204)
async def delete_contract(
    contract_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> None:
    """Delete one contract owned by the current user.

    Args:
        contract_id: Contract primary key.
        db: Request-scoped database session.
        user_id: Authenticated user id.

    Raises:
        HTTPException: 404 if the contract is missing or not owned by the user.
    """
    deleted = await contract_service.delete_contract(db, contract_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Contract not found")
    return None

