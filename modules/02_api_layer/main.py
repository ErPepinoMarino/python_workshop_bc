from fastapi import FastAPI
from api_layer.schemas import HealthResponse

app = FastAPI(title="API Layer")


@app.get("/health")
def health() -> HealthResponse:
    return HealthResponse(status="ok")
