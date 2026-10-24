# Itinerario del Bootcamp Backend con Python

**Actualizado:** 2026-10-24 · **Especificación base:** curso acordado · **Metodología:** mentoría socrática y módulos autónomos

Este documento convierte la especificación del curso en tareas pequeñas y comprobables. No sustituye a `course_scope.json`: concreta el orden de trabajo, las competencias y los criterios para dar cada módulo por terminado.

## Cómo trabajaremos

- Se asume experiencia general programando, pero no dominio de Python ni de su ecosistema. Cada sintaxis, herramienta u opción nueva se explica con un ejemplo antes de pedir que se use.
- El ciclo será: **concepto y ejemplo → cambio pequeño → comprobación → explicación de decisiones → commit/push del hito**.
- No avanzaremos de módulo solo porque el código funcione: habrá que interpretar las pruebas, explicar los errores principales y justificar decisiones básicas.
- Cada módulo tendrá su propio proyecto, dependencias, interfaz pública y pruebas. No dependerá de módulos posteriores; la conexión entre ellos se reserva al Módulo 5.
- Sin frontend. Se verificará con `pytest`, scripts de consola y, en el módulo API, Swagger UI.
- Las listas o configuraciones externas se reciben desde la capa que las conoce. Los módulos de dominio no deben asumir si los datos vienen de JSON, variables de entorno o base de datos.
- Los archivos de instrucciones originales y secretos son locales e ignorados por Git. Este itinerario es un documento del proyecto y no contiene secretos.

**Estados:** `[x]` completado y comprobado · `[~]` empezado o pendiente de una decisión · `[ ]` pendiente.

## Vista global

| Módulo | Estado | Resultado que debe quedar demostrable |
|---|---|---|
| 1. Core Tooling & Data Validation | En curso | Paquete de validación independiente, tipado, con Pydantic, pytest y mypy. |
| 2. Async REST API & Dependency Injection | Pendiente | API aislada con routers, dependencias, errores y OpenAPI; respuestas simuladas, sin base de datos. |
| 3. Async Persistence & Migrations | Pendiente | Capa de PostgreSQL asíncrona, migraciones y repositorios probados por separado. |
| 4. Background Tasks & Distributed Queues | Pendiente | Worker independiente con Redis, productor de tareas, reintentos y política de fallos. |
| 5. System Integration & Containerization | Pendiente | Monolito modular integrado y ejecutable con Docker Compose. |

---

# Módulo 1 — Core Tooling & Data Validation

**Carpeta:** `modules/01_core_validation` · **Ejecución definida:** `pytest tests/` (en este entorno, `uv run pytest tests/`).
**Competencias:** `uv`, entornos y dependencias, tipos y mypy, Pydantic v2, validadores, fixtures y parametrización de pytest.

## Estado comprobado

- Paquete aislado con `uv`, Python local 3.14 y compatibilidad declarada desde 3.12.
- Pydantic 2 como dependencia de ejecución; pytest y mypy como dependencias de desarrollo; `uv.lock` creado.
- Modelo `Producto`, tipo reutilizable `NoVacio` y función `validar_producto_para_tienda` implementados.
- **22 pruebas pasan** y `uv run mypy src/core_validation tests` no detecta problemas.
- Último hito publicado: commit `aeacece`; árbol de trabajo limpio al actualizar este plan.
- `Producto.tipo` es texto no vacío. Las categorías permitidas se pasan desde fuera; no hay una lista global ni un `Enum` fijo.
- Decisión de alcance: la unicidad y generación automática del `id` corresponden a persistencia. En este módulo se valida un `id` ya asignado; no se simula una base de datos.

## Pasos atómicos

### A. Proyecto y herramientas

- [x] A1. Revisar los objetivos del módulo y decidir que sea autónomo.
- [x] A2. Configurar Git remoto, rama `main` e ignorar entornos, secretos e instrucciones privadas.
- [x] A3. Inicializar el paquete con `uv` y elegir intérprete local y versión mínima soportada.
- [x] A4. Separar dependencias de ejecución (`pydantic`) y desarrollo (`pytest`, `mypy`).
- [x] A5. Generar y sincronizar `uv.lock` y `.venv`.
- [x] A6. Aprender a distinguir `pyproject.toml` (declaración del proyecto) de `uv.lock` (resolución reproducible).

**Competencia adquirida:** preparar un proyecto Python reproducible sin instalar sus dependencias globalmente.

### B. Bases de Python necesarias para este módulo

- [x] B1. Contrastar `float` con `Decimal` y observar por qué se construyen importes desde texto.
- [x] B2. Entender asignación, tipos dinámicos y la diferencia entre anotaciones y validación en ejecución.
- [x] B3. Leer y explicar funciones, parámetros, retornos y anotaciones como `-> str`.
- [x] B4. Leer y explicar clases, instancias, `self`, `__init__`, métodos y f-strings.
- [x] B5. Entender decoradores y distinguir la analogía con anotaciones de Spring de su mecanismo Python.
- [ ] B6. Reforzar imports, diccionarios, colecciones, excepciones y `None` cuando aparezcan en las siguientes tareas.

**Competencia adquirida:** leer y escribir las construcciones Python usadas por las herramientas del módulo, sin presuponer experiencia previa con su sintaxis.

### C. Contrato y modelo del producto

- [x] C1. Acordar campos y reglas: `id`, `nombre`, `precio`, `descripcion`, `tipo` y `marca`.
- [x] C2. Crear un modelo `BaseModel` y distinguir campos requeridos, opcionales y anulables.
- [x] C3. Validar `id >= 0` y precio `Decimal`, `> 0`, `<= 10.000.000` y hasta dos decimales.
- [x] C4. Aplicar límites de texto a nombre, marca y descripción.
- [x] C5. Reutilizar normalización y rechazo de texto en blanco con `Annotated` y `AfterValidator`.
- [x] C6. Mantener categorías de tienda fuera del modelo: quien llama aporta el conjunto permitido.
- [ ] C7. Revisar el contrato del `id` al diseñar la entrada de la API: el modelo actual representa un producto con un `id` ya asignado; una petición de creación podrá tener un esquema distinto sin `id`.

**Competencia adquirida:** separar forma y restricciones intrínsecas del producto de reglas que necesitan información externa, como el catálogo de una tienda.

### D. Validación dependiente de la tienda

- [x] D1. Definir `validar_producto_para_tienda(producto, categorias_permitidas)` fuera del modelo `Producto`.
- [x] D2. Comprobar que acepta una categoría presente en el conjunto recibido.
- [x] D3. Comprobar que rechaza una categoría no permitida.
- [x] D4. No cargar categorías desde archivos o bases de datos dentro del validador: esa responsabilidad es de quien le proporciona los datos.

**Competencia adquirida:** validar una regla que depende de dos conceptos (producto y tienda) sin hardcodear datos específicos de una tienda.

### E. Pruebas, tipos y cierre

- [x] E1. Aprender la forma básica de un test: función `test_...`, `assert` y error esperado con `pytest.raises`.
- [x] E2. Usar parametrización para ejecutar una prueba con varios precios.
- [x] E3. Cubrir límites de id, precio, nombre, marca y descripción; revisar que cada caso falle por la regla que pretende probar.
- [x] E4. Probar categorías permitidas y rechazadas por tienda.
- [ ] E5. Añadir pruebas explícitas para descripción en blanco y tipo en blanco; la regla compartida existe, pero esos campos aún no tienen un caso directo.
- [ ] E6. Aprender `@pytest.fixture` con un ejemplo pequeño y aplicarlo a datos repetidos solo después de entender qué devuelve y cómo pytest lo inyecta.
- [ ] E7. Dar nombres legibles a los casos parametrizados para que una cadena larga no inunde la salida de pytest.
- [ ] E8. Configurar mypy en el proyecto con el nivel acordado y entender qué comprueba y qué no comprueba.
- [ ] E9. Definir la interfaz pública en `src/core_validation/__init__.py` y explicar qué se importa desde el paquete.
- [ ] E10. Completar el README con instalación, uso y comando autónomo.
- [ ] E11. Verificar `uv lock --check`, `uv run pytest tests/`, mypy y construcción del paquete.
- [ ] E12. Explicar sin ayuda: `Decimal` frente a `float`; anotaciones frente a Pydantic; `Field` frente a validador; `pytest.raises`; parametrización; fixture; dependencias de desarrollo frente a ejecución.
- [ ] E13. Revisar el diff, verificar que no se incluyen secretos ni `.venv`, y hacer commit/push de cierre.

**Criterio de salida del Módulo 1:** módulo autónomo, instalable y tipado; pruebas y mypy pasan; interfaz pública y README claros; el estudiante puede explicar y modificar una regla de validación sin copiarla a ciegas.

---

# Módulo 2 — Async REST API & Dependency Injection

**Carpeta:** `modules/02_api_layer` · **Ejecución definida:** `uvicorn main:app --reload`.
**Restricción:** API aislada con respuestas simuladas; todavía no depende del módulo de persistencia ni de los demás módulos.

## Pasos atómicos

- [ ] M2.01. Crear proyecto independiente con `uv`, versión Python, dependencias de FastAPI/Uvicorn y pytest para desarrollo.
- [ ] M2.02. Crear `main.py` con una instancia mínima de FastAPI y arrancarla con el comando del módulo.
- [ ] M2.03. Añadir una ruta de salud y probar respuesta, status code y contenido con el cliente de pruebas.
- [ ] M2.04. Definir modelos de petición y respuesta locales para el API simulado; no importar el paquete de otro módulo antes de M5.
- [ ] M2.05. Añadir rutas por recurso usando `APIRouter` y separar el registro de routers de `main.py`.
- [ ] M2.06. Probar un flujo de lectura y uno de creación con respuestas simuladas y status codes apropiados.
- [ ] M2.07. Explicar `async def` y `await` con un ejemplo de ruta; distinguir I/O asíncrono de trabajo bloqueante.
- [ ] M2.08. Crear una dependencia de FastAPI con `Depends` y documentar qué recurso/configuración proporciona.
- [ ] M2.09. Inyectar una dependencia simulada en pruebas y demostrar que el endpoint no accede a servicios reales.
- [ ] M2.10. Añadir una excepción propia y un manejador global; probar el status y el cuerpo del error.
- [ ] M2.11. Añadir middleware con una responsabilidad pequeña (por ejemplo, correlación/log de petición) y probarlo.
- [ ] M2.12. Inspeccionar `/openapi.json` y `/docs`; verificar que rutas, modelos y errores públicos aparecen como se espera.
- [ ] M2.13. Ejecutar la app por consola, probar `/docs`, ejecutar pytest y mypy; documentar el comando autónomo.
- [ ] M2.14. Explicar el ciclo petición → dependencia → ruta → respuesta/error y completar commit/push del hito.

**Competencias adquiridas:** diseño HTTP, routers, modelos de entrada/salida, DI con `Depends`, async básico, errores globales, middleware y OpenAPI.

**Criterio de salida:** API aislada con respuestas mockeadas, documentación automática útil y pruebas de rutas/dependencias/errores.

---

# Módulo 3 — Async Persistence & Migrations

**Carpeta:** `modules/03_persistence` · **Ejecución definida:** `alembic upgrade head && pytest tests/`.
**Restricción:** capa de persistencia autónoma conectada a PostgreSQL; no depende del API ni del worker.

## Pasos atómicos

- [ ] M3.01. Crear un `pyproject.toml` y entorno independientes; añadir SQLAlchemy 2, driver PostgreSQL asíncrono, Alembic y herramientas de test.
- [ ] M3.02. Definir configuración de conexión desde entorno; dejar secretos fuera del repositorio y probar la configuración inválida.
- [ ] M3.03. Levantar una instancia de PostgreSQL de desarrollo y comprobar conectividad desde el módulo.
- [ ] M3.04. Crear `AsyncEngine` y explicar ciclo de vida, conexión y cierre del engine.
- [ ] M3.05. Crear `AsyncSession` y una dependencia/contexto de sesión con cierre correcto.
- [ ] M3.06. Definir `DeclarativeBase` y un modelo con `Mapped` y `mapped_column`.
- [ ] M3.07. Definir claves, nullability, índices y restricciones; separar claves generadas por la BD de datos de creación enviados por el cliente.
- [ ] M3.08. Inicializar Alembic con configuración asíncrona y conectar metadata.
- [ ] M3.09. Generar y revisar una migración inicial; aprender que una migración se inspecciona, no se acepta ciegamente.
- [ ] M3.10. Probar `upgrade`, verificar el esquema y practicar un `downgrade` controlado en desarrollo.
- [ ] M3.11. Implementar operaciones del repositorio usando sesiones asíncronas; mantener SQL/ORM fuera de rutas y modelos de entrada.
- [ ] M3.12. Probar persistencia, transacciones, rollback y errores de unicidad contra una base de pruebas aislada.
- [ ] M3.13. Probar que la base genera IDs y rechaza duplicados; esta es la prueba de unicidad que no correspondía al Módulo 1.
- [ ] M3.14. Ejecutar Alembic y pytest desde el módulo, verificar mypy y documentar configuración local.
- [ ] M3.15. Explicar `AsyncEngine`, `AsyncSession`, mappings, migraciones y repositorio; cerrar con commit/push.

**Competencias adquiridas:** mapping SQLAlchemy 2 tipado, sesiones async, transacciones, repositorios, migraciones revisables y restricciones realmente garantizadas por PostgreSQL.

**Criterio de salida:** esquema reproducible desde cero, repositorio probado contra PostgreSQL y restricciones de datos verificadas con integración.

---

# Módulo 4 — Background Tasks & Distributed Queues

**Carpeta:** `modules/04_background_jobs` · **Ejecución definida:** `arq worker.WorkerSettings`.
**Decisión de herramienta:** empezar con ARQ, porque el comando del curso la especifica; no instalar ARQ y Celery a la vez.

## Pasos atómicos

- [ ] M4.01. Crear proyecto independiente con `uv`, dependencias de ARQ/Redis y pytest.
- [ ] M4.02. Arrancar Redis local de desarrollo y configurar conexión por entorno sin guardar credenciales.
- [ ] M4.03. Comparar función síncrona, coroutine (`async def`) y tarea bloqueante con ejemplos ejecutables.
- [ ] M4.04. Explicar event loop, `await` y por qué una llamada bloqueante puede frenar tareas concurrentes.
- [ ] M4.05. Definir configuración del worker y probar startup/shutdown de conexiones.
- [ ] M4.06. Crear una tarea mínima e identificar qué datos se serializan en su payload.
- [ ] M4.07. Crear un productor que encole la tarea y verificar el resultado en Redis/worker.
- [ ] M4.08. Definir estados y comportamiento ante errores; distinguir error de negocio, error transitorio y error permanente.
- [ ] M4.09. Configurar reintentos, espera/backoff y máximo de intentos; probar el número efectivo de ejecuciones.
- [ ] M4.10. Diseñar idempotencia para que reintentar un trabajo no duplique efectos externos.
- [ ] M4.11. Definir e implementar una política de dead-letter queue compatible con ARQ; documentar si se almacena aparte, pues no se asumirá que ARQ la provee automáticamente.
- [ ] M4.12. Probar productor, worker, reintentos y fallo permanente con Redis de pruebas o dobles controlados.
- [ ] M4.13. Ejecutar el comando del worker, ejecutar pruebas y tipado; documentar cómo observar y detener el proceso.
- [ ] M4.14. Explicar concurrencia async frente a threads, retries, idempotencia y dead letters; cerrar con commit/push.

**Competencias adquiridas:** modelo productor/consumidor, Redis como broker, worker async, resiliencia, idempotencia y tratamiento explícito de fallos.

**Criterio de salida:** un proceso worker autónomo consume tareas, aplica una política de reintentos y hace observable el fallo definitivo.

---

# Módulo 5 — System Integration & Containerization

**Carpeta:** raíz del repositorio, `integrated_app/` · **Ejecución definida:** `docker compose up --build`.
**Objetivo:** integrar los módulos solo ahora, conservando responsabilidades y pruebas autónomas.

## Pasos atómicos

- [ ] M5.01. Revisar los contratos públicos de los módulos y registrar incompatibilidades antes de conectarlos.
- [ ] M5.02. Decidir cómo instalar los paquetes locales en la app integrada sin romper su ejecución autónoma (por ejemplo, dependencias editables/workspace).
- [ ] M5.03. Crear `integrated_app/` y un punto de entrada que arranque la API.
- [ ] M5.04. Componer configuración, repositorio, sesiones, clientes Redis y productor de tareas desde el borde de la aplicación.
- [ ] M5.05. Conectar rutas con servicios/repositorios sin trasladar SQL ni reglas de negocio a los routers.
- [ ] M5.06. Conectar productor de trabajos y worker; probar un flujo completo API → persistencia → cola → worker.
- [ ] M5.07. Crear Dockerfile multi-stage para la API y verificar build/run aislados.
- [ ] M5.08. Crear Dockerfile multi-stage para el worker y compartir solo lo que tenga sentido.
- [ ] M5.09. Definir servicios Docker Compose para API, worker, PostgreSQL y Redis; añadir redes y volúmenes necesarios.
- [ ] M5.10. Añadir healthchecks y dependencias de arranque sin asumir que `depends_on` significa que un servicio está listo.
- [ ] M5.11. Pasar configuración y secretos por entorno; comprobar que no se escriben en imágenes, logs ni Git.
- [ ] M5.12. Añadir logging estructurado con `structlog`, campos de correlación y pruebas/inspección de salida.
- [ ] M5.13. Implementar health/readiness checks y probar estados saludable y no disponible.
- [ ] M5.14. Ejecutar pruebas unitarias por módulo sin Compose y pruebas de integración con Compose.
- [ ] M5.15. Construir desde un checkout limpio, ejecutar `docker compose up --build` y probar el flujo end-to-end.
- [ ] M5.16. Documentar arquitectura, configuración, comandos, migraciones, workers, logs y procedimientos de diagnóstico.
- [ ] M5.17. Revisar imágenes, secretos, volúmenes, logs, pruebas y contratos; cerrar con commit/push del sistema integrado.

**Competencias adquiridas:** composición de módulos, Docker multi-stage, Compose, configuración segura, observabilidad, healthchecks y validación end-to-end.

**Criterio de salida:** sistema reproducible desde un checkout limpio, cuatro servicios coordinados y módulos aún comprobables por separado.

---

## Puertas de dominio entre módulos

Antes de avanzar de módulo se deben cumplir todas estas condiciones:

1. El comando autónomo del módulo se ejecutó y su resultado está registrado.
2. Las pruebas cubren el comportamiento normal, límites y fallos relevantes; no hay falsos positivos por otro campo inválido.
3. Las comprobaciones de tipos/lint configuradas pasan, sin afirmar validación que no se haya ejecutado.
4. El estudiante puede explicar el flujo principal, una decisión de diseño y una alternativa descartada.
5. Puede interpretar un error típico y modificar una regla/prueba sin copiar el ejemplo literalmente.
6. La interfaz pública está tipada, el README permite arrancar el módulo y no hay secretos en el diff.
7. El estado se registra aquí y el hito queda committeado y subido.

## Estado del siguiente paso

**Estamos en el Módulo 1, bloque E: cierre de cobertura y competencias de pytest.** El próximo hito es añadir los casos directos pendientes (texto en blanco en descripción/tipo) y enseñar/aplicar una fixture con datos de producto reutilizables. Después se cerrarán la interfaz pública, la configuración de mypy y el README. No se abrirá M2 hasta que se cumpla el criterio de salida de M1 y el estudiante confirme que entiende las pruebas y las decisiones.
