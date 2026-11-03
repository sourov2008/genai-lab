"""Server-rendered UI routes for listing and uploading contracts."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user_id
from app.db.session import get_db
from app.services import contract_service

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


@router.post("/contracts/upload")
async def ui_upload_contract(
    filename: str = Form(...),
    raw_text: str = Form(...),
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> RedirectResponse:
    """Create a contract from the UI form and return to the list.

    Args:
        filename: Original file name.
        raw_text: Full contract text.
        db: Request-scoped database session.
        user_id: Authenticated user id.

    Returns:
        Redirect to `/ui` after the contract is saved.
    """
    await contract_service.create_contract(
        db,
        user_id=user_id,
        filename=filename,
        raw_text=raw_text,
    )
    return RedirectResponse(url="/ui", status_code=303)
