from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from persistence.repositories import ProductoRepository


async def test_crear_producto(session: AsyncSession) -> None:
    repo = ProductoRepository(session)

    creado = await repo.crear("Pepino", Decimal("1.50"))

    assert creado.id is not None
    assert creado.nombre == "Pepino"


async def test_listar_productos(session: AsyncSession) -> None:
    repo = ProductoRepository(session)
    await repo.crear("Pepino", Decimal("1.50"))

    productos = await repo.listar()

    assert [producto.nombre for producto in productos] == ["Pepino"]


async def test_obtener_producto_inexistente(session: AsyncSession) -> None:
    repo = ProductoRepository(session)

    assert await repo.obtener(999) is None


async def test_id_duplicado_es_rechazado(session: AsyncSession) -> None:
    repo = ProductoRepository(session)
    creado = await repo.crear("Pepino", Decimal("1.50"))

    with pytest.raises(IntegrityError):
        async with session.begin_nested():
            await session.execute(
                text(
                    "INSERT INTO productos (id, nombre, precio) "
                    "VALUES (:id, :nombre, :precio)"
                ),
                {"id": creado.id, "nombre": "Otro", "precio": Decimal("2.00")},
            )
