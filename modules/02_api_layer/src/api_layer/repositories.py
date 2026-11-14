from decimal import Decimal

from api_layer.schemas import ProductoResponse


class ProductoRepository:
    def listar(self) -> list[ProductoResponse]:
        return [ProductoResponse(id=1, nombre="Pepino", precio=Decimal("1.00"))]

    def obtener(self, producto_id: int) -> ProductoResponse | None:
        return None  # mock: no hay productos por id todavía


def obtener_repositorio() -> ProductoRepository:
    return ProductoRepository()
