"""Tests de integración contra el stack levantado con Docker Compose."""

import os
import subprocess
import time
from collections.abc import Generator
from pathlib import Path

import httpx
import pytest

BASE_URL = "http://127.0.0.1:8020"
REPO_ROOT = Path(__file__).resolve().parents[3]
COMPOSE_FILE = REPO_ROOT / "modules" / "05_integrated_app" / "docker-compose.yml"


def _run(*args: str, check: bool = True) -> None:
    subprocess.run(list(args), cwd=REPO_ROOT, check=check)  # noqa: S603


@pytest.fixture(scope="module")
def compose_stack() -> Generator[None, None, None]:
    if not os.environ.get("RUN_INTEGRATION_TESTS"):
        pytest.skip("set RUN_INTEGRATION_TESTS=1 to run Docker Compose tests")

    _run("docker", "compose", "-f", str(COMPOSE_FILE), "down", "-v", check=False)
    _run("docker", "compose", "-f", str(COMPOSE_FILE), "up", "-d", "--build")

    for _ in range(30):
        try:
            response = httpx.get(f"{BASE_URL}/ready", timeout=2)
            if response.status_code == 200:
                break
        except Exception:  # noqa: BLE001
            pass
        time.sleep(2)
    else:
        _run("docker", "compose", "-f", str(COMPOSE_FILE), "logs", check=False)
        _run("docker", "compose", "-f", str(COMPOSE_FILE), "down", "-v", check=False)
        pytest.fail("el stack de Compose no estuvo listo a tiempo")

    yield

    _run("docker", "compose", "-f", str(COMPOSE_FILE), "down", "-v", check=False)


def test_crear_producto_y_encolar_compra(compose_stack: None) -> None:
    create_response = httpx.post(
        f"{BASE_URL}/products",
        json={"nombre": "Integration", "precio": "25.00"},
    )
    assert create_response.status_code == 201
    producto_id = create_response.json()["id"]

    purchase_response = httpx.post(
        f"{BASE_URL}/products/{producto_id}/comprar",
        json={},
    )
    assert purchase_response.status_code == 202

    time.sleep(5)

    detail_response = httpx.get(f"{BASE_URL}/products/{producto_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == producto_id
