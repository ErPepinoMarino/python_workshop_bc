from typing import Annotated

from fastapi import APIRouter, Depends

from api_layer.errors import ProductoNoEncontrado
from api_layer.repositories import ProductoRepository, obtener_repositorio
from api_layer.schemas import ProductoCreate, ProductoResponse

router = APIRouter(prefix="/products", tags=["products"])


@router.post("", response_model=ProductoResponse, status_code=201)
def crear_producto(payload: ProductoCreate) -> ProductoResponse:
    return ProductoResponse(
        id=1,
        nombre=payload.nombre,
        precio=payload.precio,
    )


@router.get("", response_model=list[ProductoResponse])
def listar_productos(
    repo: Annotated[ProductoRepository, Depends(obtener_repositorio)],
) -> list[ProductoResponse]:
    return repo.listar()


@router.get("/{producto_id}", response_model=ProductoResponse)
def obtener_producto(
    producto_id: int,
    repo: Annotated[ProductoRepository, Depends(obtener_repositorio)],
) -> ProductoResponse:
    producto = repo.obtener(producto_id)
    if producto is None:
        raise ProductoNoEncontrado(producto_id)
    return producto
