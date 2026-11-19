from arq.connections import ArqRedis

from background_jobs.producer import encolar_suma


async def test_encolar_suma_deja_el_job_en_cola(pool: ArqRedis) -> None:
    job = await encolar_suma(pool, 2, 3)

    assert job is not None
    en_cola = {definicion.job_id for definicion in await pool.queued_jobs()}
    assert job.job_id in en_cola
