from collections.abc import AsyncGenerator

import pytest_asyncio
from sqlalchemy.engine import URL, make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from persistence.config import get_settings


def _test_database_url() -> URL:
    return make_url(get_settings().database_url).set(database="bootcamp_test")


@pytest_asyncio.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(_test_database_url())
    async with engine.connect() as conexion:
        transaccion = await conexion.begin()
        sesion = AsyncSession(bind=conexion, expire_on_commit=False)
        try:
            yield sesion
        finally:
            await sesion.close()
            await transaccion.rollback()
    await engine.dispose()
