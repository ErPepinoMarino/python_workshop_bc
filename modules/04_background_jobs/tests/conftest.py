from collections.abc import AsyncGenerator

import pytest
from arq import create_pool
from arq.connections import ArqRedis

from background_jobs.config import get_settings


@pytest.fixture
async def pool(monkeypatch: pytest.MonkeyPatch) -> AsyncGenerator[ArqRedis, None]:
    monkeypatch.setenv("REDIS_DATABASE", "1")
    get_settings.cache_clear()
    pool = await create_pool(get_settings().to_arq())
    await pool.flushdb()
    try:
        yield pool
    finally:
        await pool.aclose()
        get_settings.cache_clear()
