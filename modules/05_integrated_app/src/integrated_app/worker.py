from decimal import Decimal
from typing import Any

from arq.connections import RedisSettings

from background_jobs.dlq import con_dlq
from integrated_app.config import get_settings
from integrated_app.database import session_scope
from integrated_app.repositories import CompraRepository, ProductoRepository
from integrated_app.services import ProductoConComprasError

MAX_INTENTOS = 3


async def procesar_compra(
    ctx: dict[str, Any],
    producto_id: int,
    importe_str: str,
    order_id: str,
) -> None:
    del ctx
    importe = Decimal(importe_str)
    async with session_scope() as session:
        repo = CompraRepository(session)
        await repo.registrar(
            order_id=order_id,
            producto_id=producto_id,
            importe=importe,
        )


async def procesar_borrado(
    ctx: dict[str, Any],
    producto_id: int,
    order_id: str,
) -> None:
    del ctx, order_id
    async with session_scope() as session:
        producto_repo = ProductoRepository(session)
        compra_repo = CompraRepository(session)

        producto = await producto_repo.obtener(producto_id)
        if producto is None:
            return

        compras = await compra_repo.contar_por_producto(producto_id)
        if compras > 0:
            raise ProductoConComprasError(producto_id)

        await producto_repo.borrar(producto_id)


class WorkerSettings:
    functions = [
        con_dlq(procesar_compra, MAX_INTENTOS),
        con_dlq(procesar_borrado, MAX_INTENTOS),
    ]
    redis_settings: RedisSettings = get_settings().to_arq()
    max_jobs = 1
    job_timeout = 30
    health_check_interval = 5
    max_tries = MAX_INTENTOS
