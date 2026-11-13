from collections.abc import Iterator
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from main import app

from api_layer.repositories import ProductoRepository, obtener_repositorio
from api_layer.schemas import ProductoResponse


class RepoFalso(ProductoRepository):
    def listar(self) -> list[ProductoResponse]:
        return [ProductoResponse(id=99, nombre="Falso", precio=Decimal("2.50"))]


@pytest.fixture
def cliente_con_repo_falso() -> Iterator[TestClient]:
    app.dependency_overrides[obtener_repositorio] = RepoFalso
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
