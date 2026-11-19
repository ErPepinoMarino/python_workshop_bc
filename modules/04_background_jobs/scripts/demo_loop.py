import asyncio
import time


async def tarea(nombre: str, bloqueante: bool) -> None:
    print(f"{nombre}: empieza")
    if bloqueante:
        time.sleep(1)
    else:
        await asyncio.sleep(1)
    print(f"{nombre}: termina")


async def medir_bloqueante() -> None:
    inicio = time.perf_counter()
    await asyncio.gather(
        tarea("A", bloqueante=True),
        tarea("B", bloqueante=True),
        tarea("C", bloqueante=True),
    )
    total = time.perf_counter() - inicio
    print(f"bloqueante: {total:.2f}s")


async def medir_asincrona() -> None:
    inicio = time.perf_counter()
    await asyncio.gather(
        tarea("A", bloqueante=False),
        tarea("B", bloqueante=False),
        tarea("C", bloqueante=False),
    )
    total = time.perf_counter() - inicio
    print(f"asíncrona: {total:.2f}s")


async def medir_mixta() -> None:
    inicio = time.perf_counter()
    await asyncio.gather(
        tarea("A", bloqueante=True),
        tarea("B", bloqueante=False),
        tarea("C", bloqueante=False),
    )
    total = time.perf_counter() - inicio
    print(f"mixta: {total:.2f}s")


async def main() -> None:
    await medir_bloqueante()
    print()
    await medir_mixta()
    print()
    await medir_asincrona()


if __name__ == "__main__":
    asyncio.run(main())
