from arq.connections import ArqRedis
from arq.jobs import Job


async def encolar_suma(pool: ArqRedis, a: int, b: int) -> Job | None:
    return await pool.enqueue_job("sumar", a, b)
