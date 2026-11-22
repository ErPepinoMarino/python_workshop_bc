import json
from collections.abc import Awaitable
from datetime import UTC, datetime
from functools import wraps
from typing import Any, cast

from arq import Retry
from arq.connections import ArqRedis
from arq.typing import WorkerCoroutine

CLAVE_DLQ = "arq:dead"
MAX_ENTRADAS = 1000


async def registrar(
    redis: ArqRedis,
    *,
    funcion: str,
    job_id: str,
    error: BaseException,
    args: dict[str, Any],
    job_try: int,
) -> None:
    entrada = {
        "funcion": funcion,
        "job_id": job_id,
        "error": f"{type(error).__name__}: {error}",
        "args": args,
        "momento": datetime.now(UTC).isoformat(),
        "job_try": job_try,
    }
    await cast(Awaitable[int], redis.lpush(CLAVE_DLQ, json.dumps(entrada)))
    await cast(Awaitable[int], redis.ltrim(CLAVE_DLQ, 0, MAX_ENTRADAS - 1))


async def listar(redis: ArqRedis, limite: int = 20) -> list[dict[str, Any]]:
    crudos = await cast(Awaitable[list[bytes]], redis.lrange(CLAVE_DLQ, 0, limite - 1))
    return [json.loads(crudo) for crudo in crudos]


def con_dlq(funcion: WorkerCoroutine, max_tries: int) -> WorkerCoroutine:
    @wraps(funcion)
    async def envoltorio(ctx: dict[str, Any], *args: Any, **kwargs: Any) -> Any:
        try:
            return await funcion(ctx, *args, **kwargs)
        except Exception as exc:
            if not isinstance(exc, Retry) or ctx["job_try"] >= max_tries:
                await registrar(
                    ctx["redis"],
                    funcion=funcion.__qualname__,
                    job_id=ctx["job_id"],
                    job_try=ctx["job_try"],
                    error=exc,
                    args={"args": list(args), "kwargs": kwargs},
                )
            raise

    return cast(WorkerCoroutine, envoltorio)


async def tomar(redis: ArqRedis, indice: int) -> dict[str, Any]:
    crudo = await cast(Awaitable[bytes | None], redis.lindex(CLAVE_DLQ, indice))
    if crudo is None:
        raise IndexError(f"no hay entrada {indice} en la DLQ")

    eliminadas = await cast(Awaitable[int], redis.lrem(CLAVE_DLQ, 1, crudo.decode()))
    if eliminadas == 0:
        raise RuntimeError("la entrada cambió mientras se leía; reintenta")

    entrada: dict[str, Any] = json.loads(crudo)
    return entrada
