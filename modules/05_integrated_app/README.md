# Módulo 5 — Integrated App

Aplicación backend integrada que demuestra cómo encajan en un mismo sistema:

- **FastAPI** como capa HTTP.
- **PostgreSQL + asyncpg + SQLAlchemy** para persistencia.
- **Redis + ARQ** para colas de trabajo asíncronas.
- **Worker asíncrono** que procesa compras y borrados.
- **CLI interactiva** con `rich` para visualizar el flujo completo.

No es una integración literal de los módulos 1–4; es una aplicación propia que aplica lo aprendido, reutilizando solo las primitivas neutras `order_id` (ahora reemplazado por UUID interno) y `con_dlq` del módulo 4.

## Stack

- Python 3.12+
- FastAPI + Uvicorn
- Pydantic + pydantic-settings
- SQLAlchemy 2 (async) + Alembic
- asyncpg
- ARQ (worker sobre Redis)
- redis-py
- httpx, rich, pyfiglet
- pytest, mypy, ruff

## Estructura

```text
modules/05_integrated_app/
├── migrations/versions/        # Migraciones Alembic
├── scripts/cli.py              # Consola interactiva y scriptable
├── src/integrated_app/
│   ├── config.py               # Variables de entorno
│   ├── database.py             # Engine, sesiones y utilidades
│   ├── main.py                 # Punto de entrada FastAPI
│   ├── models.py               # Modelos SQLAlchemy
│   ├── repositories.py         # Acceso a datos
│   ├── routes/products.py      # Endpoints HTTP
│   ├── schemas.py              # Esquemas Pydantic
│   ├── services.py             # Lógica de negocio
│   └── worker.py               # Jobs de ARQ
└── tests/
```

## Arranque de dependencias

El bootcamp asume contenedores locales:

```bash
# PostgreSQL en 127.0.0.1:5433, base de datos "integrated"
# Redis en 127.0.0.1:6379/db 0
```

Si no los tienes levantados, puedes usarlos de cualquier otra forma, pero los valores por defecto apuntan a esos hosts.

## Instalación

```bash
cd modules/05_integrated_app
uv sync
```

## Variables de entorno

Se leen desde `.env` o desde el entorno. Valores por defecto:

| Variable | Valor por defecto | Descripción |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:bootcamp@127.0.0.1:5433/integrated` | URL de PostgreSQL |
| `REDIS_HOST` | `127.0.0.1` | Host de Redis |
| `REDIS_PORT` | `6379` | Puerto de Redis |
| `REDIS_DATABASE` | `0` | Base de datos de Redis |
| `API_BASE_URL` | `http://127.0.0.1:8010` | URL de la API para el CLI |

## Migraciones

```bash
uv run alembic upgrade head
```

## Ejecutar la API

```bash
uv run uvicorn integrated_app.main:app --host 127.0.0.1 --port 8010 --reload
```

Swagger UI: `http://127.0.0.1:8010/docs`

Health: `http://127.0.0.1:8010/health`

## Ejecutar el worker

```bash
uv run arq integrated_app.worker.WorkerSettings
```

## Docker Compose

Levanta toda la pila (PostgreSQL, Redis, API y worker) desde la raíz del repo:

```bash
docker compose -f modules/05_integrated_app/docker-compose.yml up --build -d
```

Servicios expuestos:

- API: `http://127.0.0.1:8010`
- PostgreSQL: puerto interno `5432` del contenedor
- Redis: puerto interno `6379` del contenedor

El contenedor de la API aplica las migraciones de Alembic antes de arrancar Uvicorn. Tanto la API como el worker esperan a que Postgres y Redis estén healthy gracias a `depends_on` con condición.

Para parar:

```bash
docker compose -f modules/05_integrated_app/docker-compose.yml down -v
```

## CLI interactiva

```bash
uv run python scripts/cli.py
```

Muestra un menú con ASCII art y permite:

1. Crear producto
2. Listar productos
3. Ver producto por id
4. Borrar producto
5. Comprar producto
6. Simular doble compra (idempotencia)
7. Simular doble borrado
8. Estado de Redis: cola y DLQ
9. Estado de la base de datos
10. Lanzar worker y ver logs
11. Inicializar datos demo
12. Limpiar cola (Redis)
13. Ver/reintentar trabajos fallidos (DLQ)

### Worker desde el CLI

El worker se lanza dentro del propio CLI con un panel live que muestra:

- Jobs pendientes en `arq:queue`.
- Entradas en la DLQ (`arq:dead`).
- Logs recientes del worker.
- Tiempo transcurrido.

Guardas:

- Si no hay jobs en cola, no arranca.
- Si hay jobs, los procesa y se detiene automáticamente cuando la cola lleva 2 segundos vacía.

### CLI scriptable

También se pueden ejecutar comandos sin entrar al menú:

```bash
uv run python scripts/cli.py seed
uv run python scripts/cli.py listar
uv run python scripts/cli.py crear --nombre "Libreta" --precio 5.00 --tipo papelería
uv run python scripts/cli.py comprar --id 1
uv run python scripts/cli.py doble-compra --id 2
uv run python scripts/cli.py worker
uv run python scripts/cli.py bd
uv run python scripts/cli.py redis
uv run python scripts/cli.py limpiar-cola
uv run python scripts/cli.py retry-dlq --indice -1
```

## Idempotencia y `order_id`

Cada operación genera una clave compuesta:

```text
producto_id:tipo:operacion_id:modo_pago
```

Ejemplo:

```text
2:compra:c11d90586564:tarjeta
```

- `tipo` distingue compra de borrado.
- `operacion_id` es un UUID nuevo para cada operación real.
- En “doble compra” o “doble borrado” se reutiliza el mismo `operacion_id`, por lo que el worker ejecuta ambos jobs pero la base de datos solo registra uno.

## Tests

```bash
uv run pytest tests/ -q
uv run mypy
uv run ruff check .
```

## Flujo de demo recomendado

```bash
# 1. Arrancar API y worker (en terminales separadas)
uv run uvicorn integrated_app.main:app --host 127.0.0.1 --port 8010
uv run arq integrated_app.worker.WorkerSettings

# 2. En otra terminal, lanzar el CLI
uv run python scripts/cli.py

# 3. Dentro del menú
#    11 → Inicializar datos demo
#    5  → Comprar un producto
#    10 → Lanzar worker y ver logs
#    9  → Estado de la base de datos
#    6  → Simular doble compra
#    10 → Lanzar worker de nuevo
#    7  → Simular doble borrado
#    10 → Lanzar worker
#    8  → Estado de Redis
#    13 → Ver DLQ si ha fallado algo
```

## Notas

- `Limpiar cola (Redis)` borra solo Redis (`FLUSHDB`), no toca PostgreSQL.
- `Borrar producto` es síncrono y devuelve `409` si el producto tiene compras.
- `Simular doble borrado` encola dos jobs de borrado; si el producto tiene compras, ambos fallan y aparecen en la DLQ.
