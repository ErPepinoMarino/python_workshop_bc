from typing import Any

import pytest
from arq import Retry
from arq.connections import ArqRedis
from arq.worker import FailedJobs, Worker

from background_jobs.config import get_settings
from background_jobs.dlq import con_dlq, listar, registrar, tomar
from background_jobs.worker import MAX_INTENTOS, ErrorPermanente


async def fallar_siempre(ctx: dict[str, Any]) -> None:
    raise ErrorPermanente("fallo definitivo")


async def reintentar_siempre(ctx: dict[str, Any]) -> None:
    raise Retry(defer=0)


async def test_fallo_permanente_va_a_la_dlq(pool: ArqRedis) -> None:
    await pool.enqueue_job("fallar_siempre")

    worker = Worker(
        functions=[con_dlq(fallar_siempre, MAX_INTENTOS)],
        redis_settings=get_settings().to_arq(),
        max_tries=MAX_INTENTOS,
        burst=True,
    )
    try:
        with pytest.raises(FailedJobs):
            await worker.run_check()
    finally:
        await worker.close()

    entradas = await listar(pool)
    assert len(entradas) == 1
    assert entradas[0]["funcion"] == "fallar_siempre"
    assert "ErrorPermanente" in entradas[0]["error"]
    assert entradas[0]["job_try"] == 1


async def test_reintentos_agotados_registran_una_sola_entrada(pool: ArqRedis) -> None:
    await pool.enqueue_job("reintentar_siempre")

    worker = Worker(
        functions=[con_dlq(reintentar_siempre, MAX_INTENTOS)],
        redis_settings=get_settings().to_arq(),
        max_tries=MAX_INTENTOS,
        burst=True,
    )
    try:
        with pytest.raises(FailedJobs):
            await worker.run_check()
    finally:
        await worker.close()

    entradas = await listar(pool)
    assert len(entradas) == 1
    assert entradas[0]["job_try"] == MAX_INTENTOS


async def test_tomar_extrae_y_borra_la_entrada(pool: ArqRedis) -> None:
    await registrar(
        pool,
        funcion="x",
        job_id="1",
        job_try=1,
        error=ValueError("boom"),
        args={},
    )

    entrada = await tomar(pool, 0)

    assert entrada["funcion"] == "x"
    assert await listar(pool) == []


async def test_tomar_sin_entrada_falla(pool: ArqRedis) -> None:
    with pytest.raises(IndexError):
        await tomar(pool, 0)


async def test_tomar_avisa_si_otro_la_quito(
    pool: ArqRedis,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await registrar(
        pool,
        funcion="x",
        job_id="1",
        job_try=1,
        error=ValueError("boom"),
        args={},
    )

    async def lrem_cero(*args: object, **kwargs: object) -> int:
        return 0

    monkeypatch.setattr(pool, "lrem", lrem_cero)

    with pytest.raises(RuntimeError):
        await tomar(pool, 0)
