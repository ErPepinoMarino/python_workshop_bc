from fastapi import APIRouter

from api_layer.schemas import ProductoCreate, ProductoResponse

router = APIRouter(prefix="/products", tags=["products"])


@router.post("", response_model=ProductoResponse, status_code=201)
def crear_producto(payload: ProductoCreate) -> ProductoResponse:
    return ProductoResponse(
        id=1,
        nombre=payload.nombre,
        precio=payload.precio,
    )
