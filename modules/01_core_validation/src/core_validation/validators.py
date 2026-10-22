from typing import Annotated
from pydantic import AfterValidator

def no_vacio(value: str) -> str:
    if not value.strip():
        raise ValueError("No puede estar vacío")
    return value.strip()

NoVacio = Annotated[str, AfterValidator(no_vacio)]