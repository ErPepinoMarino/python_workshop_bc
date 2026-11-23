import asyncio
from decimal import Decimal

import asyncpg
from fastapi.testclient import TestClient


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


def test_health(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready(client: TestClient) -> None:
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_correlation_id_se_propaga(client: TestClient) -> None:
    response = client.get("/health", headers={"x-correlation-id": "abc123"})

    assert response.status_code == 200
    assert response.headers["x-correlation-id"] == "abc123"


def test_crear_y_listar_productos(client: TestClient) -> None:
    response = client.post(
        "/products",
        json={"nombre": "Pepino", "precio": "1.50"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["nombre"] == "Pepino"
    assert data["precio"] == "1.50"
    assert data["id"] == 1

    response = client.get("/products")

    assert response.status_code == 200
    productos = response.json()
    assert len(productos) == 1
    assert productos[0]["nombre"] == "Pepino"


def test_no_se_puede_crear_producto_duplicado(client: TestClient) -> None:
    client.post("/products", json={"nombre": "Tomate", "precio": "2.00"})

    response = client.post("/products", json={"nombre": "Tomate", "precio": "3.00"})

    assert response.status_code == 409
    assert "ya existe" in response.json()["detail"].lower()


def test_obtener_producto_existente(client: TestClient) -> None:
    client.post("/products", json={"nombre": "Tomate", "precio": "2.00"})
    response = client.get("/products/1")

    assert response.status_code == 200
    assert response.json()["nombre"] == "Tomate"


def test_obtener_producto_inexistente(client: TestClient) -> None:
    response = client.get("/products/999")

    assert response.status_code == 404


def test_borrar_producto_inexistente(client: TestClient) -> None:
    response = client.delete("/products/999")

    assert response.status_code == 404


def test_no_se_puede_borrar_producto_con_compra(client: TestClient) -> None:
    response = client.post(
        "/products",
        json={"nombre": "Lechuga", "precio": "1.20"},
    )
    producto_id = response.json()["id"]

    asyncio.run(_insertar_compra(producto_id, Decimal("1.20")))

    response = client.delete(f"/products/{producto_id}")

    assert response.status_code == 409
    assert "compras" in response.json()["detail"].lower()


def test_comprar_producto_devuelve_orden(client: TestClient) -> None:
    response = client.post(
        "/products",
        json={"nombre": "Zanahoria", "precio": "0.80"},
    )
    producto_id = response.json()["id"]

    response = client.post(
        f"/products/{producto_id}/comprar",
        json={"modo_pago": "tarjeta"},
    )

    assert response.status_code == 202
    data = response.json()
    assert data["producto_id"] == producto_id
    assert data["importe"] == "0.80"
    assert data["modo_pago"] == "tarjeta"
    assert "compra" in data["order_id"]


def test_comprar_producto_inexistente_devuelve_404(client: TestClient) -> None:
    response = client.post(
        "/products/999/comprar",
        json={"modo_pago": "tarjeta"},
    )

    assert response.status_code == 404
