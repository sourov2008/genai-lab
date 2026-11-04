"""Server-rendered UI routes for listing and uploading contracts."""

from __future__ import annotations

import io
import pathlib

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pypdf import PdfReader
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import get_current_user_id
from app.db.session import get_db
from app.llm.factory import make_llm_provider
from app.models.clause import ClauseStatus
from app.services import contract_service, extraction_service

router = APIRouter(prefix="/ui", tags=["ui"], include_in_schema=False)
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
async def ui_index(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> HTMLResponse:
    """Render the contract list page.

    Args:
        request: Incoming HTTP request for Jinja2.
        db: Request-scoped database session.
        user_id: Authenticated user id.

    Returns:
        HTML page with the current user's contracts.
    """
    total = await contract_service.get_contracts_count(db, user_id=user_id)
    contracts = await contract_service.get_contracts(
        db,
        user_id=user_id,
        limit=50,
        offset=0,
    )
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "request": request,
            "contracts": contracts,
            "total": total,
        },
    )


@router.post("/contracts/upload", response_model=None)
async def ui_upload_contract(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Create a contract from an uploaded PDF or text file and return to the list.

    Args:
        request: Incoming HTTP request for Jinja2 on duplicate-filename errors.
        file: Uploaded `.pdf` or `.txt` file.
        db: Request-scoped database session.
        user_id: Authenticated user id.

    Returns:
        Redirect to `/ui` after the contract is saved, or `index.html` with
        HTTP 400 when the filename is duplicate or the user row is missing.
    """
    content = await file.read()
    if file.filename is not None and pathlib.Path(file.filename).name.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(content))
        raw_text = "\n".join(page.extract_text() for page in reader.pages)
    else:
        raw_text = content.decode("utf-8")
    try:
        await contract_service.create_contract(db, user_id, file.filename, raw_text)
    except IntegrityError as exc:
        await db.rollback()
        error_str = str(exc.orig) if exc.orig is not None else str(exc)
        if "uq_contract_filename_user" in error_str:
            error_message = (
                "A contract with this filename already exists. "
                "Please rename your file and try again."
            )
        else:
            error_message = (
                "Database error: Missing or invalid User. "
                "(Foreign Key Violation). Please ensure the user is seeded."
            )
        total = await contract_service.get_contracts_count(db, user_id=user_id)
        contracts = await contract_service.get_contracts(
            db,
            user_id=user_id,
            limit=50,
            offset=0,
        )
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "request": request,
                "contracts": contracts,
                "total": total,
                "error_message": error_message,
            },
            status_code=400,
        )
    return RedirectResponse(url="/ui", status_code=303)


@router.get("/contracts/{contract_id}")
async def ui_contract_detail(
    request: Request,
    contract_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> HTMLResponse:
    """Render one contract and its extracted clauses.

    Args:
        request: Incoming HTTP request for Jinja2.
        contract_id: Contract primary key.
        db: Request-scoped database session.
        user_id: Authenticated user id.

    Returns:
        HTML detail page for the contract.

    Raises:
        HTTPException: 404 if the contract is missing or not owned.
    """
    contract = await contract_service.get_contract_by_id(db, contract_id, user_id)
    if contract is None:
        raise HTTPException(status_code=404, detail="Contract not found")
    return templates.TemplateResponse(
        request=request,
        name="detail.html",
        context={
            "request": request,
            "contract": contract,
        },
    )


@router.post("/contracts/{contract_id}/extract")
async def ui_extract_contract(
    contract_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> RedirectResponse:
    """Run LLM extraction for a contract and return to the detail page.

    Args:
        contract_id: Contract primary key.
        db: Request-scoped database session.
        user_id: Authenticated user id.

    Returns:
        Redirect to `/ui/contracts/{contract_id}` after extraction.

    Raises:
        HTTPException: 404 if the contract is missing or not owned.
    """
    contract = await contract_service.get_contract_by_id(db, contract_id, user_id)
    if contract is None:
        raise HTTPException(status_code=404, detail="Contract not found")
    llm = make_llm_provider(get_settings())
    await extraction_service.extract_clauses_from_contract(db, contract, llm)
    return RedirectResponse(url=f"/ui/contracts/{contract_id}", status_code=303)


@router.post("/clauses/{clause_id}/review")
async def ui_review_clause(
    clause_id: int,
    action: str = Form(...),
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> RedirectResponse:
    """Accept or reject a clause and return to its contract page.

    Args:
        clause_id: Clause primary key.
        action: Form value `accept` or `reject`.
        db: Request-scoped database session.
        user_id: Authenticated user id.

    Returns:
        Redirect to `/ui/contracts/{contract_id}` after the status update.

    Raises:
        HTTPException: 400 if `action` is invalid; 404 if the clause is missing
            or not owned.
    """
    if action == "accept":
        new_status = ClauseStatus.VERIFIED.value
    elif action == "reject":
        new_status = ClauseStatus.REJECTED.value
    else:
        raise HTTPException(status_code=400, detail="Invalid review action")
    clause = await contract_service.update_clause_status(
        db,
        clause_id,
        user_id,
        new_status,
    )
    if clause is None:
        raise HTTPException(status_code=404)
    return RedirectResponse(
        url=f"/ui/contracts/{clause.contract_id}",
        status_code=303,
    )
