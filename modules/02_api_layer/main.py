from fastapi import FastAPI

from api_layer.schemas import HealthResponse, ProductoCreate, ProductoResponse

app = FastAPI(title="API Layer")


@app.get("/health")
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/products", response_model=ProductoResponse, status_code=201)
def crear_producto(payload: ProductoCreate) -> ProductoResponse:
    return ProductoResponse(
        id=1,
        nombre=payload.nombre,
        precio=payload.precio,
    )
