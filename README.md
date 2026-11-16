# Python Backend Bootcamp

Repositorio de formación en Python backend para desarrolladores con experiencia previa en otros lenguajes. Cada módulo es un proyecto independiente, con sus dependencias, pruebas y comando de ejecución.

## Módulos

| Módulo | Contenido | Comando |
|---|---|---|
| `01_core_validation` | Validación de dominio con Pydantic v2 | `uv run pytest tests/` |
| `02_api_layer` | API REST con FastAPI y OpenAPI | `uv run uvicorn main:app --reload --port 8010` |
| `03_persistence` | PostgreSQL, SQLAlchemy 2 async y Alembic | `uv run alembic upgrade head && uv run pytest tests/` |
| 04_background_jobs | Colas y workers (pendiente) | — |
| 05 integración | Docker Compose (pendiente) | — |

## Requisitos

- Python 3.12 o posterior.
- [uv](https://docs.astral.sh/uv/).
- Docker, para los módulos con PostgreSQL o Redis.

## Ejecutar un módulo

```powershell
cd modules/01_core_validation
uv sync --locked
uv run pytest tests/
```

Cada módulo documenta en su propio `README.md` el arranque, el uso y sus decisiones.

## Calidad

CI ejecuta Ruff, mypy y pytest por módulo en cada pull request. `main` está protegida: requiere PR y checks en verde.

## Estructura

```text
modules/
  01_core_validation/
  02_api_layer/
  03_persistence/
.github/workflows/ci.yml
```
