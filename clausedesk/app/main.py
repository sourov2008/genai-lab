"""FastAPI application entrypoint."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import get_engine

logger = logging.getLogger("clausedesk")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    logger.info("Starting %s (%s)", settings.app_name, settings.app_env)
    yield
    await get_engine().dispose()
    logger.info("Shutdown complete")


app = FastAPI(title=get_settings().app_name, lifespan=lifespan)


@app.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    try:
        async with get_engine().connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception as exc:
        logger.exception("Health check database probe failed")
        return {"status": "degraded", "db": f"error: {type(exc).__name__}"}
    return {"status": "ok", "db": "ok"}
