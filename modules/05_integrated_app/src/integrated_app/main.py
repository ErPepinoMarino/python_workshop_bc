from collections.abc import AsyncGenerator, Awaitable
from contextlib import asynccontextmanager
from typing import Any, cast

import structlog
from arq import create_pool
from arq.connections import ArqRedis
from fastapi import FastAPI, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from integrated_app.config import get_settings
from integrated_app.database import get_engine
from integrated_app.logging_config import (
    configure_logging,
    correlation_id_middleware,
    get_correlation_id,
)
from integrated_app.routes.products import router as products_router
from integrated_app.schemas import HealthResponse

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    configure_logging(json_format=(settings.log_format == "json"))
    logger.info("starting_application")

    redis_pool: ArqRedis = await create_pool(settings.to_arq())
    app.state.engine = get_engine()
    app.state.redis_pool = redis_pool

    try:
        yield
    finally:
        await redis_pool.aclose()
        await app.state.engine.dispose()
        logger.info("stopping_application")


app = FastAPI(title="Integrated App", lifespan=lifespan)
app.middleware("http")(correlation_id_middleware)
app.include_router(products_router)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/ready")
async def ready(request: Request) -> dict[str, str]:
    cid = get_correlation_id()

    try:
        async with async_sessionmaker(
            request.app.state.engine, expire_on_commit=False
        )() as session:
            await session.execute(text("SELECT 1"))
    except Exception as exc:
        logger.error(
            "database_readiness_failed",
            error=str(exc),
            correlation_id=cid,
        )
        raise HTTPException(
            status_code=503, detail="database unavailable"
        ) from exc

    try:
        await cast(Awaitable[Any], request.app.state.redis_pool.ping())
    except Exception as exc:
        logger.error(
            "redis_readiness_failed",
            error=str(exc),
            correlation_id=cid,
        )
        raise HTTPException(
            status_code=503, detail="redis unavailable"
        ) from exc

    return {"status": "ok"}
