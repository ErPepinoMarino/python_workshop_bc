# API Layer

Módulo 2 del bootcamp: API REST aislada construida con FastAPI.

## Qué es y qué no es

Este módulo demuestra cómo exponer operaciones por HTTP con FastAPI: rutas, validación de entrada y salida, inyección de dependencias, manejo de errores, middleware y documentación OpenAPI.

Límites deliberados:

- **No hay persistencia.** Las respuestas son simuladas; el repositorio devuelve datos fijos en memoria.
- **No importa otros módulos** del bootcamp. La integración llega en el Módulo 5.
- **No hay autenticación.** No es una API lista para producción.
- El `id` de un producto creado es siempre `1`; no se genera ni se guarda.

## Requisitos y arranque

- Python 3.12 o posterior. El entorno local usa la versión de `.python-version`.
- [uv](https://docs.astral.sh/uv/) para gestionar entorno y dependencias.

Desde esta carpeta:

```powershell
uv sync --locked
uv run uvicorn main:app --reload --port 8010
```

- `main:app`: Uvicorn importa `main.py` y sirve la variable `app`.
- `--reload`: reinicia el servidor al guardar cambios; solo para desarrollo.
- `--port 8010`: evita el puerto `8000`, ocupado en este equipo por la detección local de vLLM de OpenCode.

Documentación interactiva: <http://127.0.0.1:8010/docs>

Contrato OpenAPI en JSON: <http://127.0.0.1:8010/openapi.json>

## Endpoints

| Método | Ruta | Códigos | Descripción |
|---|---|---|---|
| GET | `/health` | 200 | Estado del servicio |
| GET | `/products` | 200 | Lista de productos simulados |
| POST | `/products` | 201, 422 | Crea un producto simulado |
| GET | `/products/{producto_id}` | 200, 404, 422 | Detalle por id |

Ejemplos:

```powershell
curl.exe -i http://127.0.0.1:8010/products

curl.exe -i -X POST http://127.0.0.1:8010/products `
  -H "Content-Type: application/json" `
  -d '{\"nombre\":\"Pepino\",\"precio\":\"1.50\"}'
```

El precio viaja como texto (`"1.50"`) porque el modelo usa `Decimal`; así se evita perder precisión.

## Errores y cabeceras

- `422`: el cuerpo no cumple el esquema. Lo genera FastAPI antes de ejecutar la ruta (precio no positivo, nombre vacío, campo faltante, tipo incorrecto).
- `404`: producto inexistente. Lo produce la excepción de dominio `ProductoNoEncontrado`, traducida por un manejador global.
- Formato de error: `{"detail": "..."}`.
- `x-request-id`: presente en toda respuesta. Se respeta el valor enviado por el cliente o se genera un UUID v4.

## Calidad

```powershell
uv run ruff check .
uv run mypy
uv run pytest tests/ -q
```

CI ejecuta esas tres comprobaciones en cada pull request. Las pruebas usan `TestClient` y sustituyen el repositorio con `app.dependency_overrides`; no necesitan red ni base de datos.

Comando autónomo del módulo:

```powershell
uv run pytest tests/ -q
```

## Estructura

```text
main.py                  app FastAPI, middleware, /health y manejador de errores
src/api_layer/
  products.py            APIRouter y endpoints de productos
  repositories.py        repositorio en memoria (mock)
  schemas.py             modelos Pydantic de entrada, salida y error
  errors.py              excepción de dominio ProductoNoEncontrado
tests/
  conftest.py            fixture con repositorio falso y limpieza de overrides
  test_main.py           pruebas HTTP de rutas, errores, middleware y contrato
```
