from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    status: str


class ProductoCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    precio: Decimal = Field(gt=0, le=10_000_000)
    descripcion: str | None = Field(default=None, max_length=1000)
    tipo: str = Field(default="general", max_length=50)
    marca: str | None = Field(default=None, max_length=100)


class ProductoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    precio: Decimal
    descripcion: str | None
    tipo: str
    marca: str | None
    creado_en: datetime
    actualizado_en: datetime


class CompraRequest(BaseModel):
    importe: Decimal | None = Field(default=None, gt=0, le=10_000_000)
    modo_pago: str = Field(default="tarjeta", max_length=50)


class CompraResponse(BaseModel):
    order_id: str
    producto_id: int
    importe: Decimal
    modo_pago: str
