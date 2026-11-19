from typing import Any

from arq import Retry
from arq.connections import RedisSettings

from background_jobs.config import get_settings


async def on_startup(ctx: dict[str, Any]) -> None:
    print("worker arrancado")


async def on_shutdown(ctx: dict[str, Any]) -> None:
    print("worker detenido")


async def ping(ctx: dict[str, Any]) -> str:
    return "pong"


async def sumar(ctx: dict[str, Any], a: int, b: int) -> int:
    return a + b


async def cobrar(ctx: dict[str, Any], pedido_id: str) -> str:
    try:
        return await proveedor_falso(pedido_id)
    except (TimeoutError, ConnectionError) as exc:
        raise Retry(defer=ctx["job_try"] * 2) from exc


class WorkerSettings:
    functions = [ping, sumar, cobrar]
    on_startup = on_startup
    on_shutdown = on_shutdown
    redis_settings: RedisSettings = get_settings().to_arq()
    max_jobs = 1
    job_timeout = 30
    health_check_interval = 5
    max_tries = 3


class ErrorPermanente(Exception):
    """Fallo no recuperable: se deja propagar y el job falla."""


async def proveedor_falso(pedido_id: str) -> str:
    if pedido_id == "timeout":
        raise TimeoutError("el proveedor no responde")
    if pedido_id == "invalido":
        raise ErrorPermanente("importe inválido")
    return f"cobrado {pedido_id}"
