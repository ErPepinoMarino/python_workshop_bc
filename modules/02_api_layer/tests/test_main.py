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
