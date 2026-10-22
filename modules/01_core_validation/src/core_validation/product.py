from decimal import Decimal
from pydantic import BaseModel, Field
from .validators import NoVacio
class Producto(BaseModel):
    id: int = Field(ge=0)
    precio: Decimal = Field(
        gt=0,
        le=10_000_000,
        max_digits=10,
        decimal_places=2,
    )
    nombre: NoVacio = Field(max_length=100)
    marca: NoVacio = Field(max_length=50)
    tipo: NoVacio
    descripcion: NoVacio | None = Field(max_length = 5000, default=None)  #Esto es para que por defecto sea None.
