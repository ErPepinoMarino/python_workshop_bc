import asyncio
from decimal import Decimal

from persistence.database import session_scope
from persistence.repositories import ProductoRepository


async def main() -> None:
    async with session_scope() as session:
        repo = ProductoRepository(session)
        creado = await repo.crear("Pepino", Decimal("1.50"))
        print(creado.id, creado.nombre, creado.precio)

        for producto in await repo.listar():
            print(producto.id, producto.nombre, producto.precio)


if __name__ == "__main__":
    asyncio.run(main())
