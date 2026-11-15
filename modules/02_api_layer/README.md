# API Layer

API REST aislada con FastAPI. Las respuestas son simuladas: este módulo **no** se conecta a una base de datos ni importa otros módulos del bootcamp. La persistencia real llega en el Módulo 3 y la integración, en el Módulo 5.

## Requisitos

- Python 3.12 o posterior; el entorno local usa la versión de `.python-version`.
- [uv](https://docs.astral.sh/uv/) para entorno y dependencias.

## Puesta en marcha

Desde esta carpeta:

```powershell
uv sync --locked
uv run uvicorn main:app --reload --port 8010
```

- `main:app` indica módulo y variable ASGI; Uvicorn es el servidor que ejecuta la aplicación.
- `--reload` reinicia al guardar cambios (desarrollo).
- `--port 8010` evita el puerto `8000`, que en este equipo usa la detección de vLLM de OpenCode.

Documentación interactiva: <http://127.0.0.1:8010/docs>

Contrato OpenAPI: <http://127.0.0.1:8010/openapi.json>

## Endpoints

| Método | Ruta | Respuesta | Descripción |
|---|---|---|---|
| GET | `/health` | 200 | Estado del servicio |
| GET | `/products` | 200 | Lista simulada de productos |
| POST | `/products` | 201, 422 | Crea un producto simulado |
| GET | `/products/{id}` | 200, 404, 422 | Detalle simulado; 404 si no existe |

Ejemplo:

```powershell
curl.exe -i http://127.0.0.1:8010/products

curl.exe -i -X POST http://127.0.0.1:8010/products `
  -H "Content-Type: application/json" `
  -d '{\"nombre\":\"Pepino\",\"precio\":\"1.50\"}'
```

Los precios viajan como texto (`"1.50"`) porque el modelo usa `Decimal` y así se conserva la precisión.

## Errores

- `422`: el JSON no cumple el esquema (precio no positivo, nombre vacío, tipo incorrecto).
- `404`: producto inexistente; devuelve `{"detail": "..."}` y está documentado en OpenAPI.
- Toda respuesta incluye `x-request-id`: se respeta el del cliente o se genera uno.

## Calidad

```powershell
uv run ruff check .
uv run mypy
uv run pytest tests/ -q
```

Estas tres comprobaciones se ejecutan en CI para cada pull request. Las pruebas usan `TestClient` y sustituyen el repositorio con `app.dependency_overrides`, sin red ni base de datos.

## Estructura

```text
main.py                  app FastAPI, middleware, health y manejador de errores
src/api_layer/
  products.py            APIRouter y endpoints
  repositories.py        repositorio en memoria (mock)
  schemas.py             modelos Pydantic de entrada/salida
  errors.py              excepciones de dominio
tests/
  conftest.py            fixture con repositorio falso
  test_main.py           pruebas HTTP
```
