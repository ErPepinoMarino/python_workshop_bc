# Persistence

Módulo 3 del bootcamp: capa de persistencia asíncrona con PostgreSQL, SQLAlchemy 2 y Alembic.

## Qué es y qué no es

Implementa el acceso a datos de forma aislada: modelos mapeados, sesiones asíncronas, migraciones versionadas y un repositorio con operaciones básicas.

Límites deliberados:

- **No expone HTTP.** No depende del módulo de API ni del worker; la integración llega en el Módulo 5.
- **No hay lógica de negocio de la aplicación.** Valida lo que la base de datos puede garantizar (tipos, nulabilidad, clave primaria).
- **No hay autenticación ni multiusuario.** El usuario de PostgreSQL es de desarrollo.
- No se usa `create_all()`: el esquema se crea y evoluciona con migraciones.

## Requisitos

- Python 3.12 o posterior; el entorno local usa `.python-version`.
- [uv](https://docs.astral.sh/uv/).
- Docker con el daemon iniciado.

## Puesta en marcha

1. Crea el archivo de configuración local a partir del ejemplo:

   ```powershell
   Copy-Item .env.example .env
   ```

   `DATABASE_URL` usa el formato `postgresql+asyncpg://usuario:contraseña@host:puerto/base`.

2. Levanta PostgreSQL 17 en el puerto 5433:

   ```powershell
   docker run --name bootcamp-postgres `
     -e POSTGRES_PASSWORD=bootcamp `
     -e POSTGRES_DB=bootcamp `
     -p 5433:5432 `
     -d postgres:17
   ```

   El puerto 5433 evita conflictos con un PostgreSQL local en el 5432.

3. Instala dependencias y aplica migraciones:

   ```powershell
   uv sync --locked
   uv run alembic upgrade head
   ```

4. Comprueba la conexión:

   ```powershell
   uv run python scripts/check_db.py
   ```

   Debe imprimir `1`.

## Uso

```python
import asyncio
from decimal import Decimal

from persistence.database import session_scope
from persistence.repositories import ProductoRepository


async def main() -> None:
    async with session_scope() as session:
        repo = ProductoRepository(session)
        creado = await repo.crear("Pepino", Decimal("1.50"))
        print(creado.id)
        print([p.nombre for p in await repo.listar()])


asyncio.run(main())
```

- `session_scope()` abre una sesión y una transacción; hace `commit` al salir sin error y `rollback` si hay excepción.
- El repositorio hace `flush` (envía el `INSERT`) pero **no** confirma: la transacción pertenece a quien orquesta.

## Migraciones

```powershell
# Comparar modelos con la base y generar un archivo
uv run alembic revision --autogenerate -m "describe el cambio"

# Revisar el archivo generado en migrations/versions/ antes de aplicarlo
uv run alembic upgrade head

# Revertir la última migración
uv run alembic downgrade -1
```

Una migración se **revisa**: autogenerate puede omitir restricciones o proponer `DROP` inesperados. `downgrade` debe ser razonable, no un vacío.

## Pruebas

```powershell
uv run pytest tests/ -q
```

Las pruebas usan una base separada, `bootcamp_test`, y una transacción externa por test que se revierte al terminar. Así cada test empieza limpia sin `TRUNCATE`.

Preparación de la base de pruebas:

```powershell
docker exec bootcamp-postgres psql -U postgres -c "CREATE DATABASE bootcamp_test;"
$env:DATABASE_URL = "postgresql+asyncpg://postgres:bootcamp@127.0.0.1:5433/bootcamp_test"
uv run alembic upgrade head
Remove-Item Env:DATABASE_URL
```

Calidad:

```powershell
uv run ruff check .
uv run mypy
```

## Estructura

```text
alembic.ini                 configuración de Alembic (URL se sobrescribe en env.py)
migrations/
  env.py                    conecta Alembic con settings y Base.metadata
  versions/                 migraciones versionadas
src/persistence/
  config.py                 Settings desde entorno y .env; get_settings cacheado
  database.py               engine, fábrica de sesiones y session_scope
  models.py                 Base declarativa y modelo Producto
  repositories.py           ProductoRepository (crear, listar, obtener)
scripts/
  check_db.py               comprobación de conectividad
  repo_demo.py              demo manual de creación y listado
tests/
  conftest.py               fixture con transacción y rollback por test
  test_repositories.py      pruebas de repositorio y restricción de PK
```

## Decisiones y límites conocidos

- `engine` es único por proceso y mantiene un pool; la sesión se crea por unidad de trabajo.
- `expire_on_commit=False` evita consultas implícitas al acceder a atributos después del commit.
- El `id` lo genera PostgreSQL. En pruebas no se asume un valor concreto.
- `precio` es `numeric(10,2)`: 10 dígitos totales, 2 decimales.
- Pendiente para el Módulo 5: configuración de usuario con permisos mínimos y restricciones adicionales si el dominio las exige.
