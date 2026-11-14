from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from api_layer.errors import ProductoNoEncontrado
from api_layer.products import router as products_router
from api_layer.schemas import HealthResponse

app = FastAPI(title="API Layer")
app.include_router(products_router)


@app.get("/health")
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.exception_handler(ProductoNoEncontrado)
async def manejar_producto_no_encontrado(
    request: Request,
    exc: ProductoNoEncontrado,
) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})
