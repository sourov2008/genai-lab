"""FastAPI application entrypoint."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import get_engine
from app.routers.analytics import router as analytics_router
from app.routers.auth import auth_router
from app.routers.contracts import router as contracts_router
from app.routers.ui import router as ui_router
from app.routers.webhooks import router as webhooks_router

logger = logging.getLogger("clausedesk")

tags_metadata = [
    {
        "name": "auth",
        "description": "Register an account and obtain a JWT.",
    },
    {
        "name": "contracts",
        "description": "Operations with contracts. Upload, extract, and manage clauses.",
    },
    {
        "name": "meta",
        "description": "Health checks and system status.",
    },
    {
        "name": "webhooks",
        "description": "Inbound callbacks from automation tools such as n8n.",
    },
    {
        "name": "analytics",
        "description": "Usage digest for token counts, cost, and contract volume.",
    },
]

# TODO: Refactor deprecated asynccontextmanager.
@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Start and stop application resources.

    Args:
        _app: FastAPI instance (unused; required by the lifespan protocol).

    Yields:
        Control to the running application between startup and shutdown.
    """
    settings = get_settings()
    logger.info("Starting %s (%s)", settings.app_name, settings.app_env)
    yield
    await get_engine().dispose()
    logger.info("Shutdown complete")


app = FastAPI(
    title="ClauseDesk API",
    description=(
        "Contract clause extraction with verified citations. "
        "**Not a chatbot. Not legal advice.**"
    ),
    version="0.1.0",
    contact={"name": "ClauseDesk Team", "email": "api@clausedesk.com"},
    openapi_tags=tags_metadata,
    swagger_ui_parameters={"deepLinking": True, "displayRequestDuration": True},
    lifespan=lifespan,
)
app.include_router(auth_router)
app.include_router(contracts_router)
app.include_router(ui_router)
app.include_router(webhooks_router)
app.include_router(analytics_router)

_APP_DIR = Path(__file__).resolve().parent
(_APP_DIR / "templates").mkdir(parents=True, exist_ok=True)
(_APP_DIR / "static").mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Return a JSON body for request validation failures.

    Args:
        _request: Incoming request (unused).
        exc: FastAPI validation error.

    Returns:
        HTTP 422 response with error details.
    """
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "details": jsonable_encoder(exc.errors()),
        },
    )


@app.exception_handler(HTTPException)
async def custom_http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse | RedirectResponse:
    """Send unauthenticated UI visitors to login; otherwise return JSON.

    Args:
        request: Incoming request (used to detect `/ui` paths).
        exc: Raised HTTP error.

    Returns:
        Redirect to `/ui/login` for UI 401s, otherwise a JSON error body.
    """
    if request.url.path.startswith("/ui") and exc.status_code == 401:
        return RedirectResponse(url="/ui/login")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.get("/", tags=["meta"])
async def root() -> dict[str, str]:
    """Return links to docs, UI, and health.

    Returns:
        Welcome payload with relative paths for `/docs`, `/ui`, and `/health`.
    """
    return {
        "message": "Welcome to ClauseDesk API",
        "documentation": "/docs",
        "ui": "/ui",
        "health": "/health",
    }


@app.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    """Report process and database health.

    Returns:
        Status payload. `db` is `ok` when `SELECT 1` succeeds.
    """
    try:
        async with get_engine().connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception as exc:
        logger.exception("Health check database probe failed")
        return {"status": "degraded", "db": f"error: {type(exc).__name__}"}
    return {"status": "ok", "db": "ok"}
