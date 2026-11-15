from fastapi.testclient import TestClient
from main import app


def test_health() -> None:
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_post_ok() -> None:
    client = TestClient(app)
    response = client.post("/products", json={"nombre": "string", "precio": "1"})

    assert response.status_code == 201
    assert response.json() == {"id": 1, "nombre": "string", "precio": "1"}


def test_post_rechaza_precio_cero() -> None:
    client = TestClient(app)
    response = client.post(
        "/products",
        json={"nombre": "Pepino", "precio": "0"},
    )
    assert response.status_code == 422


def test_list_products_returns_mock() -> None:
    client = TestClient(app)
    response = client.get("/products")

    assert response.status_code == 200
    assert response.json() == [{"id": 1, "nombre": "Pepino", "precio": "1.00"}]


def test_list_products_usa_repositorio_inyectado(
    cliente_con_repo_falso: TestClient,
) -> None:
    response = cliente_con_repo_falso.get("/products")

    assert response.status_code == 200
    assert response.json() == [{"id": 99, "nombre": "Falso", "precio": "2.50"}]


def test_get_producto_inexistente_devuelve_404(
    cliente_con_repo_falso: TestClient,
) -> None:
    response = cliente_con_repo_falso.get("/products/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Producto 999 no encontrado"}


def test_middleware_genera_request_id() -> None:
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["x-request-id"]


def test_middleware_respeta_request_id() -> None:
    client = TestClient(app)
    response = client.get("/health", headers={"x-request-id": "abc-123"})

    assert response.headers["x-request-id"] == "abc-123"
