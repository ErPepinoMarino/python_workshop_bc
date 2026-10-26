from decimal import Decimal
import pytest
from pydantic import ValidationError
from core_validation.product import Producto


def test_normaliza_nombre()-> None:
    producto = Producto(
        id=1,
        precio=Decimal("10.00"),
        nombre=" pepino ",
        marca="Huerta",
        tipo="verdura",
    )

    assert producto.nombre == "pepino"

def test_rechaza_nombre_en_blanco()-> None:
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
def test_rechaza_precio_invalido(precio: Decimal)-> None:
    with pytest.raises(ValidationError):
        Producto(
            id=1,
            precio=precio,
            nombre="Pepino",
            marca="Huerta",
            tipo="verdura",
        )

def test_rechaza_id_invalida()-> None:
    with pytest.raises(ValidationError):
        Producto(
            id=-1,
            precio=Decimal("10.00"),
            nombre="Pepino",
            marca="Huerta",
            tipo="verdura",
        )

def test_acepta_id_cero()-> None:
    producto = Producto(
        id=0,
        precio=Decimal("10.00"),
        nombre="Pepino",
        marca="Huerta",
        tipo="verdura",
    )
    assert producto.id == 0

@pytest.mark.parametrize(
    "precio",
    [Decimal("0.01"), Decimal("10000000.00")],
)
def test_acepta_precios_limite(precio: Decimal)-> None:
    producto = Producto(
        id=1,
        precio=precio,
        nombre="Pepino",
        marca="Huerta",
        tipo="verdura",
    )

    assert producto.precio == precio

@pytest.mark.parametrize(
    "descripcion",
    ["x" * 5000, None],
)
def test_acepta_descripcion_limite(descripcion: str | None)-> None:
    producto = Producto(
        id=1,
        precio=Decimal("10.00"),
        nombre="Pepino",
        marca="Huerta",
        tipo="verdura",
        descripcion=descripcion
    )

    assert producto.descripcion == descripcion

def test_descripcion_omitida_usa_none()-> None:
    producto = Producto(
        id=1,
        precio=Decimal("10.00"),
        nombre="Pepino",
        marca="Huerta",
        tipo="verdura",
    )
    assert producto.descripcion is None

def test_rechaza_descripcion_larga()-> None:
    with pytest.raises(ValidationError):
        Producto(
            id=1,
            precio=Decimal("10.00"),
            nombre="Pepino",
            marca="Huerta",
            tipo="verdura",
            descripcion= "x"*5001
        )

def test_rechaza_descripcion_vacia()-> None:
    with pytest.raises(ValidationError):
        Producto(
            id=1,
            precio=Decimal("10.00"),
            nombre="Pepino",
            marca="Huerta",
            tipo="verdura",
            descripcion= " "
        )

@pytest.mark.parametrize(
    "nombre",
    ["x"*101, ""],
)

def test_rechaza_nombre_limite(nombre: str)-> None:
    with pytest.raises(ValidationError):
        Producto(
            id=1,
            precio=Decimal("10.00"),
            nombre=nombre,
            marca="Huerta",
            tipo="verdura",
        )

@pytest.mark.parametrize(
    "marca",
    ["x"*51, ""],
)

def test_rechaza_marca_limite(marca: str)-> None:
    with pytest.raises(ValidationError):
        Producto(
        id=1,
        precio=Decimal("10.00"),
        nombre="Pepino",
        marca=marca,
        tipo="verdura",
        )

def test_acepta_nombre_limite()-> None:
    producto = Producto(
        id=1,
        precio=Decimal("10.00"),
        nombre="x"*100,
        marca="Huerta",
        tipo="verdura",
    )
    assert producto.nombre == "x"*100

def test_acepta_marca_limite()-> None:
    producto = Producto(
        id=1,
        precio=Decimal("10.00"),
        nombre="pepino",
        marca="x"*50,
        tipo="verdura",
    )
    assert producto.marca == "x"*50

def test_rechaza_tipo_vacio()-> None:
    with pytest.raises(ValidationError):
        Producto(
            id=1,
            precio=Decimal("10.00"),
            nombre="Pepino",
            marca="Huerta",
            tipo="",
            descripcion= "x"*50
        )