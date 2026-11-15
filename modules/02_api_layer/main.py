import uuid

from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import RequestResponseEndpoint

from api_layer.errors import ProductoNoEncontrado
from api_layer.products import router as products_router
from api_layer.schemas import HealthResponse

app = FastAPI(title="API Layer")
app.include_router(products_router)


@app.middleware("http")
async def correlacion(
    request: Request,
    call_next: RequestResponseEndpoint,
) -> Response:
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    return response


@app.get("/health")
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.exception_handler(ProductoNoEncontrado)
async def manejar_producto_no_encontrado(
    request: Request,
    exc: ProductoNoEncontrado,
) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})
