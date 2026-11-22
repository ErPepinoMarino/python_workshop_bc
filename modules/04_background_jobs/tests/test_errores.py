from typing import Any

import pytest
from arq import Retry
from arq.connections import ArqRedis
from arq.worker import FailedJobs, Worker

from background_jobs.config import get_settings
from background_jobs.identidad import order_id
from background_jobs.worker import ErrorPermanente, cobrar_demo


async def test_error_transitorio_se_traduce_en_retry() -> None:
    with pytest.raises(Retry) as excinfo:
        await cobrar_demo({"job_try": 2}, "timeout")

    assert excinfo.value.defer_score == 4000


async def test_error_permanente_no_se_reintenta() -> None:
    with pytest.raises(ErrorPermanente):
        await cobrar_demo({"job_try": 1}, "invalido")


async def contar(ctx: dict[str, Any]) -> None:
    await ctx["redis"].incr("test:ejecuciones")
    raise Retry(defer=0)


async def fallar_permanente(ctx: dict[str, Any]) -> None:
    await ctx["redis"].incr("test:permanentes")
    raise ErrorPermanente("no recuperable")


async def test_max_tries_corta_en_tres(pool: ArqRedis) -> None:
    await pool.enqueue_job("contar")

    worker = Worker(
        functions=[contar],
        redis_settings=get_settings().to_arq(),
        max_tries=3,
        burst=True,
    )
    try:
        with pytest.raises(FailedJobs):
            await worker.run_check()
    finally:
        await worker.close()

    assert int(await pool.get("test:ejecuciones") or 0) == 3


async def test_error_permanente_falla_a_la_primera(pool: ArqRedis) -> None:
    await pool.enqueue_job("fallar_permanente")

    worker = Worker(
        functions=[fallar_permanente],
        redis_settings=get_settings().to_arq(),
        max_tries=3,
        burst=True,
    )
    try:
        with pytest.raises(FailedJobs):
            await worker.run_check()
    finally:
        await worker.close()

    assert int(await pool.get("test:permanentes") or 0) == 1


def test_order_id_es_estable() -> None:
    assert order_id("p1", "cobro") == "p1:cobro:v1"
    assert order_id("p1", "cobro") == order_id("p1", "cobro")


def test_operaciones_distintas_generan_claves_distintas() -> None:
    assert order_id("p1", "cobro") != order_id("p1", "reembolso")


def test_la_version_cambia_la_clave() -> None:
    assert order_id("p1", "cobro", 2) != order_id("p1", "cobro", 1)
