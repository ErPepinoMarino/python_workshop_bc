from typing import Any

from arq.connections import ArqRedis
from arq.worker import Worker

from background_jobs.config import get_settings
from background_jobs.proveedor import ProveedorPagos
from background_jobs.worker import cobrar


class ProveedorPierdeRespuesta(ProveedorPagos):
    def __init__(self, redis: ArqRedis) -> None:
        super().__init__(redis)
        self._fallado = False

    async def cobrar(self, orden_id: str, importe: int) -> str:
        cargo = await super().cobrar(orden_id, importe)
        if not self._fallado:
            self._fallado = True
            raise TimeoutError("respuesta perdida")
        return cargo


async def startup_con_fallo(ctx: dict[str, Any]) -> None:
    ctx["proveedor"] = ProveedorPierdeRespuesta(ctx["redis"])


async def test_reintento_tras_perder_la_respuesta_no_duplica_el_cobro(
    pool: ArqRedis,
) -> None:
    await pool.enqueue_job("cobrar", "pedido-1")

    worker = Worker(
        functions=[cobrar],
        on_startup=startup_con_fallo,
        redis_settings=get_settings().to_arq(),
        max_tries=3,
        burst=True,
    )
    try:
        completados = await worker.run_check()
    finally:
        await worker.close()

    assert completados == 1
    assert await ProveedorPagos(pool).total_cargos() == 1
