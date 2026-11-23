import asyncio
from collections.abc import Generator

import asyncpg
import pytest
import redis.asyncio as redis
from fastapi.testclient import TestClient

from integrated_app.main import app


async def _truncar() -> None:
    conn = await asyncpg.connect(
        "postgresql://postgres:bootcamp@127.0.0.1:5433/integrated"
    )
    try:
        await conn.execute("TRUNCATE compras, productos RESTART IDENTITY CASCADE;")
    finally:
        await conn.close()

    r = redis.Redis(host="127.0.0.1", port=6379, db=0)
    try:
        await r.flushdb()
    finally:
        await r.aclose()


@pytest.fixture(autouse=True)
def limpiar_bd() -> Generator[None]:
    """Trunca las tablas y limpia Redis después de cada test."""
    yield
    asyncio.run(_truncar())


@pytest.fixture
def client() -> Generator[TestClient]:
    with TestClient(app) as c:
        yield c
