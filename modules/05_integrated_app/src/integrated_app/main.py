from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from arq import create_pool
from arq.connections import ArqRedis
from fastapi import FastAPI

from integrated_app.config import get_settings
from integrated_app.database import get_engine
from integrated_app.routes.products import router as products_router
from integrated_app.schemas import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    redis_pool: ArqRedis = await create_pool(settings.to_arq())

    app.state.engine = get_engine()
    app.state.redis_pool = redis_pool

    try:
        yield
    finally:
        await redis_pool.aclose()
        await app.state.engine.dispose()


app = FastAPI(title="Integrated App", lifespan=lifespan)
app.include_router(products_router)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")
