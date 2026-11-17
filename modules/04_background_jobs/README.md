# Background Jobs

Módulo 4 del bootcamp: cola de trabajos distribuida con Redis, worker asíncrono, reintentos, idempotencia y dead-letter queue.

**Estado:** documento de diseño cerrado. La implementación (M4.01 en adelante) aún no existe; este README se completará con comandos, estructura y pruebas cuando el módulo funcione.

## Qué es y qué no es

Implementa el camino de un trabajo que **nace en un proceso y se ejecuta en otro**: un productor encola, Redis almacena, un worker independiente consume, reintenta y registra el resultado.

Límites deliberados:

- **No expone HTTP.** No depende del módulo de API ni del de persistencia; la integración llega en el Módulo 5.
- **No usa PostgreSQL.** El módulo es autónomo y su única infraestructura es Redis. El "pedido" y el "proveedor de pagos" son **simulados** dentro del módulo; lo que es real son las garantías: entrega, reintentos, idempotencia y fallo definitivo.
- **No usa Celery.** El comando del curso fija ARQ, y no se instalan dos gestores de colas a la vez.
- No hay frontend ni autenticación.

## Conceptos que este módulo demuestra

| Concepto | Dónde se ve |
|---|---|
| Broker, productor y consumidor como procesos distintos | Contenedor Redis + script productor + worker |
| Serialización al cruzar la frontera | El job se guarda como bytes; solo viajan datos |
| Semántica **at-least-once** | ARQ no borra el job hasta éxito o fallo definitivo |
| Bloqueo del event loop | Demo con `time.sleep` frente a `await` |
| Reintento con backoff | `arq.Retry(defer=...)` y `max_tries` |
| Idempotencia | Clave estable por operación contra un receptor que deduplica |
| Dead-letter queue | Cola propia en Redis + script de inspección y replay |

## Modelo de identidad

**Dos identificadores, no cinco.** `pedido_id` identifica la entidad; `order_id` identifica **la operación** sobre ella y se deriva de ella. Todo lo demás es `order_id`.

| Identificador | Fórmula | Quién lo genera | Cuánto vive | Dónde se guarda |
|---|---|---|---|---|
| `pedido_id` | `uuid7()` | El borde que crea el pedido | años | Registro del pedido; se devuelve al cliente |
| `order_id` | `{pedido_id}:{operacion}:{version}` | Derivado, determinista | mientras exista el pedido | Columna del registro / se recalcula |
| `job_id` (ARQ) | `order_id` | Derivado | TTL del resultado (1 h por defecto) | Redis |
| `idempotency_key` (proveedor) | `order_id` | Derivado | >= 24 h en el proveedor | Se **envía** en la petición |
| `correlation_id` | `uuid4()` por petición | Borde HTTP (M2) | minutos | Logs |

**Principio:** la clave nace con la **intención**, no con el **intento**. Y una intención es **pedido + operación + versión**, no el pedido a secas.

- Por qué la operación: cobro, reembolso y reenvío sobre el mismo pedido son operaciones distintas. Con `pedido_id` a secas, el reembolso recibiría la respuesta del cobro.
- Por qué la versión: una operación puede repetirse legítimamente (reintento comercial tras un rechazo, reenvío meses después). Sin `version`, la clave está gastada para siempre y el proveedor devuelve la respuesta vieja. Se incrementa explícitamente al abrir una **nueva** intención.
- La versión es **por operación**, no global: `pedido:1234:cobro:v2` y `pedido:1234:reembolso:v1` conviven. Reintentar un reembolso no altera la clave del cobro.
- `job_id = order_id` da una ventaja gratis: ARQ rechaza encolar un job con un id ya existente (`enqueue_job` devuelve `None`), así que el doble encolado de la misma operación se bloquea solo.
- El pedido se crea y se **commitea en estado `pending`** antes de encolar y antes de cualquier llamada al proveedor. Si el proceso muere después, la dirección (`order_id`) sigue existiendo y se puede reintentar sin ambigüedad.
- Un reintento **no** genera una clave nueva: reutiliza la guardada.
- El doble clic en "confirmar pedido" puede crear dos pedidos antes de que exista ninguno. La deduplicación de esa creación corresponde al borde (clave en la petición de creación + `UNIQUE`). Se documenta aquí; se implementará al integrar (M5).
- `correlation_id` **no** se colapsa: una petición HTTP puede tocar varios pedidos y un pedido recibe muchas peticiones a lo largo de su vida. Agrupa logs de **un flujo**, no deduplica operaciones.

### Ventanas que deben encajar

| Qué | Vida |
|---|---|
| `job_id` en Redis | 1 h por defecto |
| `order_id` | años |
| Clave en el proveedor | >= 24 h |

Si un job lleva tres días en la DLQ y se relanza con la misma `order_id`, el proveedor ya olvidó la clave y **cobraría otra vez**. Por eso: reintentos acotados, alerta en la DLQ y, al hacer replay, subir `version` o verificar contra el proveedor antes de relanzar.


## Máquina de estados

### Del pedido (nuestro, simulado en este módulo)

```
pending ──claim atómico──> processing ──éxito──> completed
   ^                           │
   │                           └──fallo definitivo──> failed
   └──lease vencido (barrido)──┘
```

- **Claim atómico:** una sola sentencia que solo cambia de estado si sigue en `pending`. Es un *check-then-act* prohibido: leer y escribir por separado permite que dos workers reclamen a la vez.
- **Lease:** `processing` incluye `lease_hasta`. Si el worker muere, el lease vence y un barrido devuelve el pedido a `pending`. Sin lease, un pedido queda atascado para siempre (falta de *liveness*).
- El lease se elige **corto** precisamente porque la clave de idempotencia hace que un reintento prematuro sea inofensivo.

### Del job (de ARQ, no nuestro)

`deferred`, `queued`, `in_progress`, `complete`, `not_found`. No se reimplementan: se consultan. Nuestros estados de negocio viven aparte.

## Reintentos

| Tipo de fallo | Ejemplo | Política |
|---|---|---|
| Transitorio | timeout de red, proveedor 503, Redis momentáneamente caído | Reintentar con espera creciente (`Retry(defer=intento * 5)`) |
| Permanente | payload inválido, pedido inexistente, error de negocio | No reintentar: `failed` y a la DLQ |
| Ambiguo | el worker murió durante la llamada | Reintentar con **la misma clave** |

- `max_tries=5` por defecto en ARQ; se configura explícitamente y se prueba el número **efectivo** de ejecuciones.
- `job_timeout` (300 s por defecto) acota un job colgado. Se fija explícitamente.
- Un `except Exception` genérico que convierte todo en reintento es un antipatrón: reintentar un `ValueError` cinco veces no arregla el payload.

## Idempotencia

Regla: **la deduplicación vive en el sistema que produce el efecto**, no en el worker.

- **Efecto interno** (misma base de datos): una transacción + restricción `UNIQUE`. No hay ventana de ambigüedad.
- **Efecto externo** (proveedor): `idempotency_key` que **viaja en la petición**. Si el receptor no coopera, no hay garantía; solo mitigaciones.
- **Receptor sin soporte** (correo): se elige explícitamente entre riesgo de duplicado y riesgo de pérdida, se documenta elección y coste, y se registra el intento para reconciliar.
- **Efecto secundario no idempotente** (descontar stock, incrementar un contador): requiere su propia protección; la clave del pago no lo cubre.

## Dead-letter queue

ARQ **no** la provee. Se implementa propia, en Redis, para no añadir infraestructura al módulo:

- Clave `arq:dead` con el payload original, el nombre de la función, el número de intentos, el tipo y mensaje de error y los timestamps.
- Script `scripts/dlq.py` con dos operaciones: **listar** y **replay** (reencolar tras corregir la causa).
- Retención acotada. Una DLQ sin límite es una fuga de memoria; una DLQ que nadie mira es un cementerio.
- Alerta: la existencia de entradas en la DLQ es un incidente operativo, no ruido.

Trade-off documentado: en un sistema con datos de negocio (M5), la DLQ se movería a un almacén consultable con SQL. Aquí se prioriza la autonomía del módulo.

## Reconciliación (deuda consciente)

La DLQ recoge fallos **conocidos**. Un fallo ambiguo que acabó bien en el proveedor y mal en nuestro registro no aparece ahí. La red de seguridad es un proceso de **reconciliación**: comparar los movimientos del proveedor con el registro local y corregir discrepancias.

En M4 **no se implementa**; se documenta qué se compararía, con qué frecuencia y qué se haría al encontrar una diferencia. La clave de idempotencia existe para que la mayoría de casos no lleguen nunca aquí.

## Decisiones y alternativas descartadas

| Decisión | Alternativa descartada | Motivo |
|---|---|---|
| ARQ | Celery | Comando del curso; asyncio nativo; no duplicar infraestructura |
| ARQ | RQ, Dramatiq, TaskIQ | Misma razón; se documentan como opciones reales en producción |
| Redis como broker | RabbitMQ, SQS | Un solo servicio, ya disponible en Docker, suficiente para el alcance |
| `max_jobs=1` al empezar | `max_jobs=10` | Razonar sin concurrencia y demostrar el bloqueo después |
| Corrutinas en un proceso | Proceso por job | El trabajo del módulo es E/S; menos memoria y conexiones. Para CPU se usará `ProcessPoolExecutor` |
| DLQ en Redis | DLQ en PostgreSQL | Autonomía del módulo: una sola infraestructura |

## Riesgos conocidos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Llamada bloqueante dentro de un job | Congela todas las tareas del worker | Disciplina async, `job_timeout`, demo explícita |
| Crash nativo / OOM | Muere el worker y los jobs en curso | Reintento tras lease vencido; varios contenedores |
| `pickle` por defecto | Deserializar un payload manipulado ejecuta código | Redis privado con contraseña; serializador alternativo documentado |
| Redis sin persistencia | Se pierde la cola al reiniciar | Configurar AOF en el contenedor de desarrollo |
| Duplicados por at-least-once | Efectos repetidos | Clave de idempotencia + `UNIQUE` en efectos internos |

## Comandos previstos

```powershell
# Redis de desarrollo (puerto 6379, sin contraseña: solo local)
docker run --name bootcamp-redis -p 6379:6379 -d redis:7-alpine

# Worker
uv run arq worker.WorkerSettings

# Productor
uv run python scripts/producer.py

# Pruebas
uv run pytest tests/
```

## Glosario

- **Broker:** proceso que almacena los trabajos hasta que alguien los consume.
- **Productor:** quien encola. **Consumidor/worker:** quien ejecuta.
- **At-least-once:** se garantiza al menos una ejecución; los duplicados son posibles por diseño.
- **Lease:** permiso temporal para ejecutar algo, con vencimiento; permite recuperar trabajo huérfano.
- **Idempotencia:** repetir una operación produce el mismo efecto que hacerla una vez.
- **DLQ:** almacén terminal para trabajos que no pudieron completarse.
- **Reconciliación:** comparación posterior entre el registro propio y la fuente de verdad externa.
