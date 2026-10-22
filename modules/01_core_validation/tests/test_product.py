from decimal import Decimal
import pytest
from pydantic import ValidationError
from core_validation.product import Producto


def test_normaliza_nombre():
    producto = Producto(
        id=1,
        precio=Decimal("10.00"),
        nombre=" pepino ",
        marca="Huerta",
        tipo="verdura",
    )

    assert producto.nombre == "pepino"

def test_rechaza_nombre_en_blanco():
    with pytest.raises(ValidationError):
        Producto(
            id=1,
            precio=Decimal("10.00"),
            nombre="   ",
            marca="Huerta",
            tipo="verdura",
        )

@pytest.mark.parametrize(
    "precio",
    [Decimal("0"), Decimal("-1"), Decimal("10000000.01"), Decimal("1.001")],
)
def test_rechaza_precio_invalido(precio):
    with pytest.raises(ValidationError):
        Producto(
            id=1,
            precio=precio,
            nombre="Pepino",
            marca="Huerta",
            tipo="verdura",
        )
