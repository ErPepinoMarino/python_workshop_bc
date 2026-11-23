import asyncio
from decimal import Decimal
from typing import cast

import asyncpg
import pytest

from integrated_app.database import close_engine
from integrated_app.services import ProductoConComprasError
from integrated_app.worker import procesar_borrado, procesar_compra


async def _crear_producto(nombre: str, precio: Decimal) -> int:
    conn = await asyncpg.connect(
        "postgresql://postgres:bootcamp@127.0.0.1:5433/integrated"
    )
    try:
        row = await conn.fetchrow(
            "INSERT INTO productos (nombre, precio, tipo) VALUES ($1, $2, 'general') RETURNING id;",
            nombre,
            precio,
        )
        assert row is not None
        return cast(int, row["id"])
    finally:
        await conn.close()


async def _contar_compras(producto_id: int) -> int:
    conn = await asyncpg.connect(
        "postgresql://postgres:bootcamp@127.0.0.1:5433/integrated"
    )
    try:
        row = await conn.fetchrow(
            "SELECT COUNT(*) FROM compras WHERE producto_id = $1;",
            producto_id,
        )
        assert row is not None
        return cast(int, row["count"])
    finally:
        await conn.close()


async def _insertar_compra(producto_id: int, importe: Decimal) -> None:
    conn = await asyncpg.connect(
        "postgresql://postgres:bootcamp@127.0.0.1:5433/integrated"
    )
    try:
        await conn.execute(
            "INSERT INTO compras (order_id, producto_id, importe) VALUES ($1, $2, $3);",
            f"{producto_id}:compra:abc123:tarjeta",
            producto_id,
            importe,
        )
    finally:
        await conn.close()


async def _producto_existe(producto_id: int) -> bool:
    conn = await asyncpg.connect(
        "postgresql://postgres:bootcamp@127.0.0.1:5433/integrated"
    )
    try:
        row = await conn.fetchrow(
            "SELECT 1 FROM productos WHERE id = $1;",
            producto_id,
        )
        return row is not None
    finally:
        await conn.close()


async def _procesar_compra_dos_veces(
    producto_id: int,
    importe: Decimal,
    order_id: str,
) -> int:
    await procesar_compra({}, producto_id, str(importe), order_id)
    await procesar_compra({}, producto_id, str(importe), order_id)
    count = await _contar_compras(producto_id)
    await close_engine()
    return count


def test_procesar_compra_es_idempotente() -> None:
    producto_id = asyncio.run(_crear_producto("Pepino", Decimal("1.50")))
    order_id = f"{producto_id}:compra:abc123:tarjeta"

    count = asyncio.run(
        _procesar_compra_dos_veces(producto_id, Decimal("1.50"), order_id)
    )

    assert count == 1


async def _procesar_borrado_dos_veces(producto_id: int, order_id: str) -> bool:
    await procesar_borrado({}, producto_id, order_id)
    await procesar_borrado({}, producto_id, order_id)
    existe = await _producto_existe(producto_id)
    await close_engine()
    return existe


def test_procesar_borrado_elimina_producto() -> None:
    producto_id = asyncio.run(_crear_producto("Borrable", Decimal("2.00")))
    order_id = f"{producto_id}:borrado:abc123:tarjeta"

    existe = asyncio.run(_procesar_borrado_dos_veces(producto_id, order_id))

    assert not existe


async def _intentar_borrar_con_compras(
    producto_id: int, order_id: str
) -> None:
    await procesar_borrado({}, producto_id, order_id)
    await close_engine()


def test_procesar_borrado_falla_si_hay_compras() -> None:
    producto_id = asyncio.run(_crear_producto("ConCompra", Decimal("3.00")))
    asyncio.run(_insertar_compra(producto_id, Decimal("3.00")))
    order_id = f"{producto_id}:borrado:abc123:tarjeta"

    with pytest.raises(ProductoConComprasError):
        asyncio.run(_intentar_borrar_con_compras(producto_id, order_id))

    assert asyncio.run(_producto_existe(producto_id))
