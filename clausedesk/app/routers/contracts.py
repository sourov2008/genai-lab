"""HTTP routes for uploading and listing contracts."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user_id
from app.db.session import get_db
from app.llm.base import LLMProvider
from app.llm.factory import get_llm
from app.schemas.clause import ClauseResponse
from app.schemas.contract import (
    ContractDetailResponse,
    ContractUpdate,
    ContractUploadResponse,
    PaginatedContractResponse,
)
from app.services import contract_service, extraction_service

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


@router.get("/", response_model=PaginatedContractResponse)
async def list_contracts(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: str | None = Query(None, description="Filter by contract status"),
) -> PaginatedContractResponse:
    """List contracts owned by the current user.

    Args:
        db: Request-scoped database session.
        user_id: Authenticated user id.
        limit: Page size (1–100).
        offset: Number of rows to skip.
        status: Optional status filter.

    Returns:
        Paginated contract summaries.
    """
    total = await contract_service.get_contracts_count(
        db,
        user_id=user_id,
        status=status,
    )
    contracts = await contract_service.get_contracts(
        db,
        user_id=user_id,
        limit=limit,
        offset=offset,
        status=status,
    )
    return PaginatedContractResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=[ContractUploadResponse.model_validate(c) for c in contracts],
    )


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


@router.patch("/{contract_id}", response_model=ContractDetailResponse)
async def update_contract(
    contract_id: int,
    payload: ContractUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> ContractDetailResponse:
    """Update selected fields on a contract owned by the current user.

    Args:
        contract_id: Contract primary key.
        payload: Optional filename, raw_text, and status.
        db: Request-scoped database session.
        user_id: Authenticated user id.

    Returns:
        Updated contract detail.

    Raises:
        HTTPException: 404 if missing or not owned; 409 on filename conflict.
    """
    contract = await contract_service.get_contract_by_id(db, contract_id, user_id)
    if contract is None:
        raise HTTPException(status_code=404, detail="Contract not found")
    try:
        contract = await contract_service.update_contract(
            db,
            contract,
            filename=payload.filename,
            raw_text=payload.raw_text,
            status=payload.status,
        )
    except IntegrityError as exc:
        raise HTTPException(
            status_code=409,
            detail="Filename already exists for this user",
        ) from exc
    return ContractDetailResponse.model_validate(contract)


@router.post("/{contract_id}/extract", response_model=list[ClauseResponse])
async def extract_contract(
    contract_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
    llm: LLMProvider = Depends(get_llm),
) -> list[ClauseResponse]:
    """Extract clauses from a contract using the configured LLM.

    Args:
        contract_id: Contract primary key.
        db: Request-scoped database session.
        user_id: Authenticated user id.
        llm: Injected LLM provider.

    Returns:
        Extracted clauses mapped from SQLAlchemy models.

    Raises:
        HTTPException: 404 if the contract is missing or not owned by the user.
    """
    contract = await contract_service.get_contract_by_id(db, contract_id, user_id)
    if contract is None:
        raise HTTPException(status_code=404, detail="Contract not found")
    clauses = await extraction_service.extract_clauses_from_contract(
        db, contract, llm
    )
    return clauses


