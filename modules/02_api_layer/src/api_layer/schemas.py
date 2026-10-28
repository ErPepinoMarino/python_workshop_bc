from decimal import Decimal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str


class ProductoCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    precio: Decimal = Field(gt=0, le=10_000_000)


class ProductoResponse(BaseModel):
    id: int
    nombre: str
    precio: Decimal
