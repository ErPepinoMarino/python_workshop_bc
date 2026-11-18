from arq import create_pool
from arq.connections import ArqRedis

from background_jobs.config import get_settings


async def test_redis_responde() -> None:
    pool: ArqRedis = await create_pool(get_settings().to_arq())
    try:
        assert await pool.ping()
    finally:
        await pool.aclose()
