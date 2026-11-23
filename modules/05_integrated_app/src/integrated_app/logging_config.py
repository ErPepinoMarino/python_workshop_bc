"""Configuración de logging estructurado con structlog y correlation ID."""

import uuid
from collections.abc import Awaitable, Callable
from contextvars import ContextVar

import structlog
from fastapi import Request, Response

correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")


def configure_logging(*, json_format: bool = False) -> None:
    processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.ExtraAdder(),
    ]

    if json_format:
        processors.extend([
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ])
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(20),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_correlation_id() -> str:
    cid = correlation_id.get()
    if not cid:
        cid = uuid.uuid4().hex[:16]
        correlation_id.set(cid)
    return cid


async def correlation_id_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    cid = request.headers.get("x-correlation-id") or uuid.uuid4().hex[:16]
    correlation_id.set(cid)
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(correlation_id=cid)
    response = await call_next(request)
    response.headers["x-correlation-id"] = cid
    return response
