from collections.abc import Awaitable
from typing import cast

from arq.connections import ArqRedis

CLAVE_CARGOS = "proveedor:cargos"


class ProveedorPagos:
    def __init__(self, redis: ArqRedis) -> None:
        self._redis = redis

    async def cobrar(self, orden_id: str, importe: int) -> str:
        valor = str(importe)
        creado = await cast(
            Awaitable[bool],
            self._redis.hsetnx(CLAVE_CARGOS, orden_id, valor),
        )
        if creado:
            return f"ch_{orden_id}"

        existente = await cast(
            Awaitable[bytes | None],
            self._redis.hget(CLAVE_CARGOS, orden_id),
        )
        if existente is None or existente.decode() != valor:
            raise RuntimeError(f"la clave {orden_id} ya existe con otros parámetros")
        return f"ch_{orden_id}"

    async def total_cargos(self) -> int:
        return await cast(Awaitable[int], self._redis.hlen(CLAVE_CARGOS))
