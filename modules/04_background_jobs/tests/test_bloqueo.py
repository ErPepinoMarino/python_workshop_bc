import asyncio
import time
from typing import Any

from arq.connections import ArqRedis
from arq.worker import Worker

from background_jobs.config import get_settings

eventos: list[str] = []


async def trabajo(ctx: dict[str, Any], nombre: str, bloqueante: bool) -> None:
    eventos.append(f"{nombre}:inicio")
    if bloqueante:
        time.sleep(0.2)
    else:
        await asyncio.sleep(0.2)
    eventos.append(f"{nombre}:fin")


async def test_job_bloqueante_no_deja_avanzar_al_otro(pool: ArqRedis) -> None:
    eventos.clear()
    await pool.enqueue_job("trabajo", "A", True)
    await pool.enqueue_job("trabajo", "B", True)

    worker = Worker(
        functions=[trabajo],
        redis_settings=get_settings().to_arq(),
        max_jobs=2,
        burst=True,
        poll_delay=0.01,
    )
    try:
        completados = await worker.run_check()
    finally:
        await worker.close()

    assert completados == 2
    assert eventos == ["A:inicio", "A:fin", "B:inicio", "B:fin"]


async def test_jobs_async_se_intercalan(pool: ArqRedis) -> None:
    eventos.clear()
    await pool.enqueue_job("trabajo", "A", False)
    await pool.enqueue_job("trabajo", "B", False)

    worker = Worker(
        functions=[trabajo],
        redis_settings=get_settings().to_arq(),
        max_jobs=2,
        burst=True,
        poll_delay=0.01,
    )
    try:
        completados = await worker.run_check()
    finally:
        await worker.close()

    assert completados == 2
    assert all(evento.endswith(":inicio") for evento in eventos[:2])
