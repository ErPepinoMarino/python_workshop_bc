# Core Validation

Paquete Python autónomo para validar datos de dominio con Pydantic v2.

## Contrato

- `Producto` valida un producto con un `id` ya asignado, nombre, marca, tipo, precio y descripción opcional.
- El precio debe ser mayor que cero, no superar 10.000.000 y tener como máximo dos decimales.
- Nombre y marca no pueden estar vacíos; sus límites son 100 y 50 caracteres, respectivamente. La descripción puede omitirse o ser `None`; si contiene texto, admite hasta 5000 caracteres.
- `validar_producto_para_tienda(producto, categorias_permitidas)` comprueba que el tipo esté permitido por esa tienda. Las categorías las proporciona quien llama; este paquete no las carga desde archivos ni bases de datos.
- La generación y unicidad del `id` corresponden a la capa de persistencia, no a este módulo.

## Requisitos y entorno

- Python 3.12 o posterior; el entorno local usa la versión indicada en `.python-version`.
- Dependencias declaradas en `pyproject.toml` y versiones resueltas en `uv.lock`.

Desde esta carpeta, sincroniza el entorno y ejecuta las comprobaciones:

```text
uv sync --locked
uv run pytest tests/
uv run mypy src/core_validation tests
```

`--locked` usa el lockfile existente y falla si está desactualizado respecto a `pyproject.toml`; no lo modifica.

## Interfaz pública

```python
from core_validation import Producto, validar_producto_para_tienda
```

Para construir el paquete localmente:

```text
uv build
```

Esto genera un wheel y un archivo fuente en `dist/`; no publica el paquete en ningún índice.
