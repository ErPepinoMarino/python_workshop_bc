import asyncio
import sys

from arq import create_pool
from arq.connections import ArqRedis

from background_jobs.config import get_settings
from background_jobs.dlq import listar, tomar


async def listar_entradas(redis: ArqRedis) -> None:
    entradas = await listar(redis)
    if not entradas:
        print("DLQ vacía")
        return

    for indice, entrada in enumerate(entradas):
        print(
            f"[{indice}] {entrada['momento']} {entrada['funcion']} try={entrada['job_try']}"
        )
        print(f"     job_id={entrada['job_id']}")
        print(f"     error={entrada['error']}")
        print(f"     args={entrada['args']}")


async def reencolar(redis: ArqRedis, indice: int) -> None:
    entrada = await tomar(redis, indice)
    job = await redis.enqueue_job(
        entrada["funcion"],
        *entrada["args"]["args"],
        **entrada["args"]["kwargs"],
    )
    if job is None:
        print("no se encoló: job_id duplicado")
    else:
        print(f"reencolado {job.job_id}: {entrada['funcion']}")


async def main() -> None:
    comando = sys.argv[1] if len(sys.argv) > 1 else "list"

    redis = await create_pool(get_settings().to_arq())
    try:
        if comando == "list":
            await listar_entradas(redis)
        elif comando == "replay":
            if len(sys.argv) < 3:
                print("uso: dlq_cli.py replay <indice>")
                raise SystemExit(2)
            try:
                indice = int(sys.argv[2])
            except ValueError:
                print("el índice debe ser un número")
                raise SystemExit(2) from None
            await reencolar(redis, indice)
        else:
            print(f"comando desconocido: {comando}")
            raise SystemExit(2)
    finally:
        await redis.aclose()


asyncio.run(main())
