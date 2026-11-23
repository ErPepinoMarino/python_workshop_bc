from collections.abc import Sequence
from decimal import Decimal
from uuid import uuid4

from arq.connections import ArqRedis
from sqlalchemy.ext.asyncio import AsyncSession

from integrated_app.models import Producto
from integrated_app.repositories import CompraRepository, ProductoRepository


class ProductoNoEncontradoError(Exception):
    def __init__(self, producto_id: int) -> None:
        self.producto_id = producto_id
        super().__init__(f"Producto {producto_id} no encontrado")


class ProductoConComprasError(Exception):
    def __init__(self, producto_id: int) -> None:
        self.producto_id = producto_id
        super().__init__(f"Producto {producto_id} tiene compras asociadas")


class ProductoDuplicadoError(Exception):
    def __init__(self, nombre: str) -> None:
        self.nombre = nombre
        super().__init__(f"Ya existe un producto con el nombre '{nombre}'")


class ProductoService:
    def __init__(self, session: AsyncSession, redis_pool: ArqRedis) -> None:
        self._productos = ProductoRepository(session)
        self._compras = CompraRepository(session)
        self._redis_pool = redis_pool

    async def crear(
        self,
        nombre: str,
        precio: Decimal,
        *,
        descripcion: str | None = None,
        tipo: str = "general",
        marca: str | None = None,
    ) -> Producto:
        existente = await self._productos.obtener_por_nombre(nombre)
        if existente is not None:
            raise ProductoDuplicadoError(nombre)

        producto = await self._productos.crear(
            nombre=nombre,
            precio=precio,
            descripcion=descripcion,
            tipo=tipo,
            marca=marca,
        )
        return producto

    async def listar(self) -> Sequence[Producto]:
        return await self._productos.listar()

    async def obtener(self, producto_id: int) -> Producto:
        producto = await self._productos.obtener(producto_id)
        if producto is None:
            raise ProductoNoEncontradoError(producto_id)
        return producto

    async def borrar(self, producto_id: int) -> bool:
        producto = await self._productos.obtener(producto_id)
        if producto is None:
            raise ProductoNoEncontradoError(producto_id)
        compras = await self._compras.contar_por_producto(producto_id)
        if compras > 0:
            raise ProductoConComprasError(producto_id)
        return await self._productos.borrar(producto_id)

    async def comprar(
        self,
        producto_id: int,
        importe: Decimal | None = None,
        *,
        modo_pago: str = "tarjeta",
    ) -> str:
        producto = await self._productos.obtener(producto_id)
        if producto is None:
            raise ProductoNoEncontradoError(producto_id)

        if importe is None:
            importe = producto.precio

        operacion_id = uuid4().hex[:12]
        order_id = f"{producto_id}:compra:{operacion_id}:{modo_pago}"
        await self._redis_pool.enqueue_job(
            "procesar_compra",
            producto_id,
            str(importe),
            order_id,
        )
        return order_id
