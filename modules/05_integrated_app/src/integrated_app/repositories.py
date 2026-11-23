from collections.abc import Sequence
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from integrated_app.models import Compra, Producto


class ProductoRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def crear(
        self,
        nombre: str,
        precio: Decimal,
        *,
        descripcion: str | None = None,
        tipo: str = "general",
        marca: str | None = None,
    ) -> Producto:
        producto = Producto(
            nombre=nombre,
            precio=precio,
            descripcion=descripcion,
            tipo=tipo,
            marca=marca,
        )
        self._session.add(producto)
        await self._session.flush()
        await self._session.refresh(producto)
        return producto

    async def listar(self) -> Sequence[Producto]:
        resultado = await self._session.execute(select(Producto).order_by(Producto.id))
        return resultado.scalars().all()

    async def obtener(self, producto_id: int) -> Producto | None:
        return await self._session.get(Producto, producto_id)

    async def obtener_por_nombre(self, nombre: str) -> Producto | None:
        result = await self._session.execute(
            select(Producto).where(Producto.nombre == nombre)
        )
        return result.scalar_one_or_none()

    async def borrar(self, producto_id: int) -> bool:
        producto = await self._session.get(Producto, producto_id)
        if producto is None:
            return False
        await self._session.delete(producto)
        return True


class CompraRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def contar_por_producto(self, producto_id: int) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(Compra)
            .where(Compra.producto_id == producto_id)
        )
        return result.scalar_one()

    async def registrar(
        self,
        order_id: str,
        producto_id: int,
        importe: Decimal,
    ) -> Compra:
        insert_stmt = (
            insert(Compra)
            .values(order_id=order_id, producto_id=producto_id, importe=importe)
            .on_conflict_do_nothing(index_elements=["order_id"])
        )
        await self._session.execute(insert_stmt)

        result = await self._session.execute(
            select(Compra).where(Compra.order_id == order_id)
        )
        return result.scalar_one()
