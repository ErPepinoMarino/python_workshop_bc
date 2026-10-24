from decimal import Decimal

import pytest

from core_validation.product import Producto
from core_validation.store_validation import validar_producto_para_tienda


def test_acepta_categoria_permitida_por_tienda():
    producto = Producto(
        id=1,
        precio=Decimal("10.00"),
        nombre="Pepino",
        marca="Huerta",
        tipo="frutas y verdura",
    )

    validar_producto_para_tienda(producto, {"frutas y verdura", "charcuteria"})


def test_rechaza_categoria_no_permitida_por_tienda():
    producto = Producto(
        id=1,
        precio=Decimal("10.00"),
        nombre="Pepino",
        marca="Huerta",
        tipo="frutas y verdura",
    )

    with pytest.raises(ValueError):
        validar_producto_para_tienda(producto, {"carnes envasadas", "charcuteria"})
