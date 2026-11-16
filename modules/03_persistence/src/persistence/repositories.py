from collections.abc import Sequence
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from persistence.models import Producto


class ProductoRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def crear(self, nombre: str, precio: Decimal) -> Producto:
        producto = Producto(nombre=nombre, precio=precio)
        self._session.add(producto)
        await self._session.flush()
        await self._session.refresh(producto)
        return producto

    async def listar(self) -> Sequence[Producto]:
        resultado = await self._session.execute(select(Producto).order_by(Producto.id))
        return resultado.scalars().all()

    async def obtener(self, producto_id: int) -> Producto | None:
        return await self._session.get(Producto, producto_id)
