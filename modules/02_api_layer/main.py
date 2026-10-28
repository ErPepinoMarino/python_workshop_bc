from fastapi import FastAPI

from api_layer.products import router as products_router
from api_layer.schemas import HealthResponse

app = FastAPI(title="API Layer")
app.include_router(products_router)


@app.get("/health")
def health() -> HealthResponse:
    return HealthResponse(status="ok")
