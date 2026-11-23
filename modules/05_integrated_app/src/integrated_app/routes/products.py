from typing import Annotated

from arq.connections import ArqRedis
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from integrated_app.database import get_session
from integrated_app.schemas import (
    CompraRequest,
    CompraResponse,
    ProductoCreate,
    ProductoResponse,
)
from integrated_app.services import (
    ProductoConComprasError,
    ProductoDuplicadoError,
    ProductoNoEncontradoError,
    ProductoService,
)

router = APIRouter(prefix="/products", tags=["products"])


async def _get_redis_pool(request: Request) -> ArqRedis:
    pool = request.app.state.redis_pool
    if not isinstance(pool, ArqRedis):
        raise RuntimeError("redis pool no inicializado")
    return pool


async def _get_service(
    session: Annotated[AsyncSession, Depends(get_session)],
    redis_pool: Annotated[ArqRedis, Depends(_get_redis_pool)],
) -> ProductoService:
    return ProductoService(session, redis_pool)


@router.post("", response_model=ProductoResponse, status_code=status.HTTP_201_CREATED)
async def crear_producto(
    payload: ProductoCreate,
    service: Annotated[ProductoService, Depends(_get_service)],
) -> ProductoResponse:
    try:
        producto = await service.crear(
            nombre=payload.nombre,
            precio=payload.precio,
            descripcion=payload.descripcion,
            tipo=payload.tipo,
            marca=payload.marca,
        )
    except ProductoDuplicadoError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    return ProductoResponse.model_validate(producto)


@router.get("", response_model=list[ProductoResponse])
async def listar_productos(
    service: Annotated[ProductoService, Depends(_get_service)],
) -> list[ProductoResponse]:
    productos = await service.listar()
    return [ProductoResponse.model_validate(p) for p in productos]


@router.get("/{producto_id}", response_model=ProductoResponse)
async def obtener_producto(
    producto_id: int,
    service: Annotated[ProductoService, Depends(_get_service)],
) -> ProductoResponse:
    try:
        producto = await service.obtener(producto_id)
    except ProductoNoEncontradoError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    return ProductoResponse.model_validate(producto)


@router.delete("/{producto_id}", status_code=status.HTTP_204_NO_CONTENT)
async def borrar_producto(
    producto_id: int,
    service: Annotated[ProductoService, Depends(_get_service)],
) -> None:
    try:
        await service.borrar(producto_id)
    except ProductoNoEncontradoError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ProductoConComprasError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.post(
    "/{producto_id}/comprar",
    response_model=CompraResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def comprar_producto(
    producto_id: int,
    payload: CompraRequest,
    service: Annotated[ProductoService, Depends(_get_service)],
) -> CompraResponse:
    try:
        order_id = await service.comprar(
            producto_id,
            payload.importe,
            modo_pago=payload.modo_pago,
        )
    except ProductoNoEncontradoError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    importe = payload.importe
    if importe is None:
        producto = await service.obtener(producto_id)
        importe = producto.precio

    return CompraResponse(
        order_id=order_id,
        producto_id=producto_id,
        importe=importe,
        modo_pago=payload.modo_pago,
    )
