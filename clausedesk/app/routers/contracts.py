"""HTTP routes for uploading and listing contracts."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.llm.base import LLMProvider
from app.llm.embeddings import get_embedding
from app.llm.errors import LLMBadRequestError
from app.llm.factory import get_llm
from app.models import User
from app.schemas.clause import ClauseResponse
from app.schemas.contract import (
    ContractDetailResponse,
    ContractUpdate,
    ContractUploadResponse,
    PaginatedContractResponse,
)
from app.services import contract_service, extraction_service
from app.services.contract_service import search_clauses_by_vector

router = APIRouter(prefix="/contracts", tags=["contracts"])


@router.post("/", response_model=ContractUploadResponse)
async def upload_contract(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ContractUploadResponse:
    """Create a contract from a multipart file upload (n8n-compatible).

    Args:
        file: Uploaded contract file (`multipart/form-data` field name `file`).
        db: Request-scoped database session.
        current_user: Authenticated user.

    Returns:
        The created contract summary.

    Raises:
        HTTPException: 400 if the filename is missing or the bytes are not UTF-8 text.
    """
    filename = file.filename
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must include a filename",
        )
    content = await file.read()
    try:
        raw_text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be UTF-8 text",
        ) from exc
    contract = await contract_service.create_contract(
        db,
        user_id=current_user.id,
        filename=filename,
        raw_text=raw_text,
    )
    return ContractUploadResponse.model_validate(contract)


@router.get("/", response_model=PaginatedContractResponse)
async def list_contracts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: str | None = Query(None, description="Filter by contract status"),
) -> PaginatedContractResponse:
    """List contracts owned by the current user.

    Args:
        db: Request-scoped database session.
        current_user: Authenticated user.
        limit: Page size (1–100).
        offset: Number of rows to skip.
        status: Optional status filter.

    Returns:
        Paginated contract summaries.
    """
    total = await contract_service.get_contracts_count(
        db,
        user_id=current_user.id,
        status=status,
    )
    contracts = await contract_service.get_contracts(
        db,
        user_id=current_user.id,
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


@router.get("/search", response_model=list[ClauseResponse])
async def search_contracts(
    q: str = Query(..., description="Search query"),
    limit: int = 5,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ClauseResponse]:
    """Return clauses nearest to the query embedding.

    Args:
        q: Natural-language search text.
        limit: Maximum number of clauses to return.
        db: Request-scoped database session.
        current_user: Authenticated user.

    Returns:
        Ranked clause payloads. Embedding-only; not stored as a prompt run.
    """
    query_vector = await get_embedding(q)
    clauses = await search_clauses_by_vector(db, query_vector, limit)
    return [ClauseResponse.model_validate(clause) for clause in clauses]


@router.get("/{contract_id}", response_model=ContractDetailResponse)
async def get_contract(
    contract_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ContractDetailResponse:
    """Return one contract owned by the current user.

    Args:
        contract_id: Contract primary key.
        db: Request-scoped database session.
        current_user: Authenticated user.

    Returns:
        Contract detail including source text and clauses.

    Raises:
        HTTPException: 404 if the contract is missing or not owned by the user.
    """
    contract = await contract_service.get_contract_by_id(db, contract_id, current_user.id)
    if contract is None:
        raise HTTPException(status_code=404, detail="Contract not found")
    return ContractDetailResponse.model_validate(contract)


@router.delete("/{contract_id}", status_code=204)
async def delete_contract(
    contract_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete one contract owned by the current user.

    Args:
        contract_id: Contract primary key.
        db: Request-scoped database session.
        current_user: Authenticated user.

    Raises:
        HTTPException: 404 if the contract is missing or not owned by the user.
    """
    deleted = await contract_service.delete_contract(db, contract_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Contract not found")
    return None


@router.patch("/{contract_id}", response_model=ContractDetailResponse)
async def update_contract(
    contract_id: int,
    payload: ContractUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ContractDetailResponse:
    """Update selected fields on a contract owned by the current user.

    Args:
        contract_id: Contract primary key.
        payload: Optional filename, raw_text, and status.
        db: Request-scoped database session.
        current_user: Authenticated user.

    Returns:
        Updated contract detail.

    Raises:
        HTTPException: 404 if missing or not owned; 409 on filename conflict.
    """
    contract = await contract_service.get_contract_by_id(db, contract_id, current_user.id)
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
    current_user: User = Depends(get_current_user),
    llm: LLMProvider = Depends(get_llm),
) -> list[ClauseResponse]:
    """Extract clauses from a contract using the configured LLM.

    Args:
        contract_id: Contract primary key.
        db: Request-scoped database session.
        current_user: Authenticated user.
        llm: Injected LLM provider.

    Returns:
        Extracted clauses mapped from SQLAlchemy models.

    Raises:
        HTTPException: 404 if the contract is missing or not owned; 500 if the
            LLM output is invalid after retries.
    """
    contract = await contract_service.get_contract_by_id(db, contract_id, current_user.id)
    if contract is None:
        raise HTTPException(status_code=404, detail="Contract not found")
    try:
        clauses = await extraction_service.extract_clauses_from_contract(
            db, contract, llm
        )
    except LLMBadRequestError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    return clauses


