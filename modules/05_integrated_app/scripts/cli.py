import argparse
import asyncio
import contextlib
import os
import sys
import time
from collections import deque
from decimal import Decimal, InvalidOperation
from typing import Any, Awaitable, cast
from uuid import uuid4

import asyncpg
import httpx
import pyfiglet
import redis.asyncio as redis
from arq import create_pool
from arq.connections import ArqRedis
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.prompt import IntPrompt, Prompt
from rich.table import Table

from background_jobs import dlq
from integrated_app.config import get_settings

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]

BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8010")
DATABASE_DSN = "postgresql://postgres:bootcamp@127.0.0.1:5433/integrated"

PRODUCTOS_DEMO: list[dict[str, Any]] = [
    {"nombre": "Portátil", "precio": "1200.00", "tipo": "electrónica"},
    {"nombre": "Ratón", "precio": "25.00", "tipo": "electrónica"},
    {"nombre": "Teclado", "precio": "75.50", "tipo": "electrónica"},
    {"nombre": "Monitor", "precio": "300.00", "tipo": "electrónica"},
    {"nombre": "Auriculares", "precio": "120.00", "tipo": "electrónica"},
    {"nombre": "Webcam", "precio": "60.00", "tipo": "electrónica"},
    {"nombre": "Silla de oficina", "precio": "250.00", "tipo": "mobiliario"},
    {"nombre": "Escritorio", "precio": "180.00", "tipo": "mobiliario"},
    {"nombre": "Lámpara", "precio": "35.00", "tipo": "decoración"},
    {"nombre": "Alfombrilla", "precio": "15.00", "tipo": "accesorio"},
]

console = Console()


def _titulo() -> None:
    fig = pyfiglet.Figlet(font="small")
    ascii_art = fig.renderText("Python Backend")
    console.print(
        Panel(
            ascii_art,
            style="bold cyan",
            expand=False,
        )
    )
    console.print(
        Panel(
            "Backend integrando Posgresql, Redis, ARQ y un worker asíncrono con asyncpg. ",
            style="dim",
            expand=False,
        )
    )
    console.print()


def _menu(queue_len: int = 0) -> None:
    opciones: list[tuple[str, str]] = [
        ("1", "Crear producto"),
        ("2", "Listar productos"),
        ("3", "Ver producto por id"),
        ("4", "Borrar producto"),
        ("5", "Comprar producto"),
        ("6", "Simular doble compra (idempotencia)"),
        ("7", "Simular doble borrado"),
        ("8", "Estado de Redis: cola y DLQ"),
        ("9", "Estado de la base de datos"),
        ("10", f"Lanzar worker y ver logs (cola: {queue_len})"),
        ("11", "Inicializar datos demo"),
        ("12", "Limpiar cola (Redis)"),
        ("13", "Ver/reintentar trabajos fallidos (DLQ)"),
        ("0", "Salir"),
    ]
    table = Table.grid(padding=(0, 2))
    table.add_column(style="bold")
    table.add_column()
    for key, desc in opciones:
        table.add_row(f"[{key}]", desc)
    console.print(Panel(table, title="Menú principal", style="bold blue"))


def _generar_order_id(
    producto_id: int,
    tipo: str,
    *,
    modo_pago: str = "tarjeta",
    operacion_id: str | None = None,
) -> str:
    if operacion_id is None:
        operacion_id = uuid4().hex[:12]
    return f"{producto_id}:{tipo}:{operacion_id}:{modo_pago}"


def _mostrar_respuesta(response: httpx.Response) -> None:
    if response.status_code < 400:
        console.print(f"[green]✓ {response.status_code}[/green] {response.text}")
    else:
        console.print(f"[red]✗ {response.status_code}[/red] {response.text}")


def _preguntar_decimal(mensaje: str) -> Decimal:
    while True:
        valor = Prompt.ask(mensaje)
        try:
            return Decimal(valor)
        except InvalidOperation:
            console.print("[red]Introduce un número válido (por ejemplo, 12.50).[/red]")


def _normalizar_opcional(valor: str) -> str | None:
    return valor if valor.strip() else None


class Consola:
    """Cliente interactivo y scriptable para probar la aplicación."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self.client = client

    async def crear_producto(
        self,
        nombre: str,
        precio: str,
        descripcion: str | None = None,
        tipo: str = "general",
        marca: str | None = None,
    ) -> httpx.Response:
        payload: dict[str, Any] = {
            "nombre": nombre,
            "precio": precio,
            "tipo": tipo,
        }
        if descripcion is not None:
            payload["descripcion"] = descripcion
        if marca is not None:
            payload["marca"] = marca

        response = await self.client.post("/products", json=payload)
        _mostrar_respuesta(response)
        return response

    async def listar_productos(self) -> None:
        response = await self.client.get("/products")
        if response.status_code != 200:
            _mostrar_respuesta(response)
            return

        productos = response.json()
        table = Table(title="Productos", show_lines=True)
        table.add_column("id", justify="right")
        table.add_column("nombre")
        table.add_column("precio", justify="right")
        table.add_column("tipo")
        for p in productos:
            table.add_row(
                str(p["id"]),
                p["nombre"],
                p["precio"],
                p["tipo"],
            )
        console.print(table)

    async def ver_producto(self, producto_id: int) -> None:
        response = await self.client.get(f"/products/{producto_id}")
        _mostrar_respuesta(response)

    async def borrar_producto(self, producto_id: int) -> None:
        response = await self.client.delete(f"/products/{producto_id}")
        _mostrar_respuesta(response)

    async def comprar_producto(
        self,
        producto_id: int,
        importe: Decimal | None = None,
    ) -> None:
        payload: dict[str, Any] = {}
        if importe is not None:
            payload["importe"] = str(importe)

        response = await self.client.post(
            f"/products/{producto_id}/comprar", json=payload
        )
        _mostrar_respuesta(response)

    async def _obtener_producto_o_error(
        self, producto_id: int
    ) -> dict[str, Any] | None:
        response = await self.client.get(f"/products/{producto_id}")
        if response.status_code == 404:
            console.print(f"[red]El producto {producto_id} no existe.[/red]")
            return None
        if response.status_code != 200:
            _mostrar_respuesta(response)
            return None
        return cast(dict[str, Any], response.json())

    async def simular_doble_compra(self, producto_id: int) -> None:
        producto = await self._obtener_producto_o_error(producto_id)
        if producto is None:
            return

        importe = Decimal(producto["precio"])
        order_id = _generar_order_id(producto_id, "compra")
        settings = get_settings()
        pool: ArqRedis = await create_pool(settings.to_arq())
        try:
            for i in range(2):
                await pool.enqueue_job(
                    "procesar_compra",
                    producto_id,
                    str(importe),
                    order_id,
                )
                console.print(
                    f"[yellow]Encolado intento {i + 1}[/yellow] → order_id={order_id}"
                )
            console.print(
                f"\n[cyan]Cuando lances el worker se intentará comprar dos veces "
                f"'{producto['nombre']}' (id={producto_id}). Solo se registrará una.[/cyan]"
            )
        finally:
            await pool.aclose()

    async def simular_doble_borrado(self, producto_id: int) -> None:
        producto = await self._obtener_producto_o_error(producto_id)
        if producto is None:
            return

        order_id = _generar_order_id(producto_id, "borrado")
        settings = get_settings()
        pool: ArqRedis = await create_pool(settings.to_arq())
        try:
            for i in range(2):
                await pool.enqueue_job(
                    "procesar_borrado",
                    producto_id,
                    order_id,
                )
                console.print(
                    f"[yellow]Encolado intento {i + 1}[/yellow] → order_id={order_id}"
                )
            console.print(
                f"\n[cyan]Cuando lances el worker se intentará borrar dos veces "
                f"'{producto['nombre']}' (id={producto_id}). La segunda será ignorada.[/cyan]"
            )
        finally:
            await pool.aclose()

    async def estado_redis(self) -> None:
        settings = get_settings()
        r = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_database,
        )
        try:
            queue_exists = await r.exists("arq:queue")
            queue_len = await r.zcard("arq:queue") if queue_exists else 0
            dlq_len = await cast(Awaitable[int], r.llen("arq:dead"))
            result_keys = await r.keys("arq:result:*")

            table = Table(title="Estado de Redis", show_lines=True)
            table.add_column("Clave/ métrica")
            table.add_column("Valor")
            table.add_row("arq:queue (jobs pendientes)", str(queue_len))
            table.add_row("arq:dead (DLQ)", str(dlq_len))
            table.add_row(
                "arq:result:* (resultados guardados)",
                str(len(result_keys)),
            )
            console.print(table)

            if queue_len:
                jobs = await r.zrange("arq:queue", 0, 9, withscores=True)
                console.print("\n[bold]Primeros jobs en cola:[/bold]")
                for job_id, score in jobs:
                    console.print(f"  {job_id.decode()} @ {score}")

            dlq_entries = await dlq.listar(r, limite=10)
            if dlq_entries:
                console.print("\n[bold]Últimas entradas en DLQ:[/bold]")
                for entrada in dlq_entries:
                    console.print(f"  {entrada['job_id']} → {entrada['error']}")
        finally:
            await r.aclose()

    async def estado_bd(self) -> None:
        conn = await asyncpg.connect(DATABASE_DSN)
        try:
            productos = await conn.fetch(
                "SELECT id, nombre, precio, tipo FROM productos ORDER BY id;"
            )
            compra_counts_rows = await conn.fetch(
                "SELECT producto_id, COUNT(*) AS count FROM compras GROUP BY producto_id;"
            )
            compra_counts = {
                row["producto_id"]: row["count"] for row in compra_counts_rows
            }
            compras = await conn.fetch(
                "SELECT id, order_id, producto_id, importe FROM compras ORDER BY id;"
            )

            table = Table(title="Productos", show_lines=True)
            table.add_column("id", justify="right")
            table.add_column("nombre")
            table.add_column("precio", justify="right")
            table.add_column("tipo")
            table.add_column("compras", justify="right")
            for p in productos:
                count = compra_counts.get(p["id"], 0)
                style = "green" if count > 0 else None
                table.add_row(
                    str(p["id"]),
                    p["nombre"],
                    str(p["precio"]),
                    p["tipo"],
                    str(count),
                    style=style,
                )
            console.print(table)

            table = Table(title="Compras", show_lines=True)
            table.add_column("id", justify="right")
            table.add_column("order_id")
            table.add_column("producto_id", justify="right")
            table.add_column("importe", justify="right")
            for c in compras:
                table.add_row(
                    str(c["id"]),
                    c["order_id"],
                    str(c["producto_id"]),
                    str(c["importe"]),
                )
            console.print(table)
        finally:
            await conn.close()

    async def inicializar_demo(self, forzar: bool = False) -> None:
        response = await self.client.get("/products")
        if response.status_code != 200:
            _mostrar_respuesta(response)
            return

        existentes = response.json()
        if existentes and not forzar:
            confirm = Prompt.ask(
                "Ya existen productos. ¿Sobrescribir datos demo? (s/N)",
                default="n",
            )
            if confirm.lower() != "s":
                console.print("[yellow]Operación cancelada.[/yellow]")
                return

        for datos in PRODUCTOS_DEMO:
            await self.client.post("/products", json=datos)

        console.print(
            f"[green]✓ {len(PRODUCTOS_DEMO)} productos de demo inicializados.[/green]"
        )

    async def limpiar_cola(self) -> None:
        settings = get_settings()
        r = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_database,
        )
        try:
            await r.flushdb()
            console.print("[green]✓ Cola de Redis limpia.[/green]")
        finally:
            await r.aclose()

    async def reintentar_dlq(self, indice: int = -1) -> None:
        settings = get_settings()
        pool: ArqRedis = await create_pool(settings.to_arq())
        try:
            entradas = await dlq.listar(pool, limite=20)
            if not entradas:
                console.print(
                    "[yellow]La cola de mensajes muertos (DLQ) está vacía. "
                    "Aquí aparecerán los jobs que fallen tras los reintentos.[/yellow]"
                )
                return

            table = Table(title="DLQ", show_lines=True)
            table.add_column("#", justify="right")
            table.add_column("función")
            table.add_column("job_id")
            table.add_column("error")
            for i, entrada in enumerate(entradas):
                table.add_row(
                    str(i),
                    entrada["funcion"],
                    entrada["job_id"],
                    entrada["error"],
                )
            console.print(table)

            if indice == -1:
                reintentos = len(entradas)
                for _ in range(reintentos):
                    entrada = await dlq.tomar(pool, 0)
                    await pool.enqueue_job(
                        entrada["funcion"],
                        *entrada["args"]["args"],
                    )
                    console.print(f"[green]Reencolado[/green] {entrada['job_id']}")
            else:
                entrada = await dlq.tomar(pool, indice)
                await pool.enqueue_job(
                    entrada["funcion"],
                    *entrada["args"]["args"],
                )
                console.print(f"[green]Reencolado[/green] {entrada['job_id']}")
        finally:
            await pool.aclose()


async def _queue_length() -> int:
    settings = get_settings()
    r = redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_database,
    )
    try:
        queue_exists = await r.exists("arq:queue")
        return await r.zcard("arq:queue") if queue_exists else 0
    finally:
        await r.aclose()


async def lanzar_worker() -> None:
    queue_len = await _queue_length()
    if queue_len == 0:
        console.print(
            "[yellow]No hay trabajos en cola. "
            "Encola una compra o simulación primero.[/yellow]"
        )
        return

    console.print(
        Panel(
            "Arrancando worker en modo live...\n"
            "Presiona [bold]Ctrl+C[/bold] para detenerlo antes de tiempo.",
            style="bold green",
        )
    )

    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "arq",
        "integrated_app.worker.WorkerSettings",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    lines: deque[str] = deque(maxlen=20)

    async def _leer_stream(stream: asyncio.StreamReader) -> None:
        while True:
            line = await stream.readline()
            if not line:
                break
            lines.append(line.decode("utf-8", errors="replace").rstrip())

    assert proc.stdout is not None
    assert proc.stderr is not None
    stdout_task = asyncio.create_task(_leer_stream(proc.stdout))
    stderr_task = asyncio.create_task(_leer_stream(proc.stderr))

    settings = get_settings()
    r = redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_database,
    )
    inicio = time.monotonic()
    empty_since: float | None = None
    GRACE_PERIOD = 2.0
    try:
        with Live(refresh_per_second=2) as live:
            while proc.returncode is None:
                queue_exists = await r.exists("arq:queue")
                queue_len = await r.zcard("arq:queue") if queue_exists else 0
                dlq_len = await cast(Awaitable[int], r.llen("arq:dead"))
                elapsed = time.monotonic() - inicio

                if queue_len == 0:
                    if empty_since is None:
                        empty_since = time.monotonic()
                    elif time.monotonic() - empty_since >= GRACE_PERIOD:
                        break
                else:
                    empty_since = None

                log_text = "\n".join(lines) if lines else "(sin logs)"
                live.update(
                    Panel(
                        f"[bold]Cola:[/bold] {queue_len}  "
                        f"[bold]DLQ:[/bold] {dlq_len}  "
                        f"[bold]Tiempo:[/bold] {elapsed:.1f}s\n\n{log_text}",
                        title="Worker",
                        style="bold green",
                    )
                )
                await asyncio.sleep(0.5)
    except asyncio.CancelledError:
        pass
    finally:
        stdout_task.cancel()
        stderr_task.cancel()
        with contextlib.suppress(ProcessLookupError):
            proc.kill()
        await proc.wait()
        await r.aclose()
        console.print("[yellow]Worker detenido.[/yellow]")


async def _main_interactivo(consola: Consola) -> None:
    _titulo()
    while True:
        queue_len = await _queue_length()
        _menu(queue_len)
        opcion = IntPrompt.ask("Elige una opción", default=0)

        try:
            if opcion == 1:
                nombre = Prompt.ask("Nombre del producto")
                precio = str(_preguntar_decimal("Precio"))
                descripcion = _normalizar_opcional(
                    Prompt.ask("Descripción (opcional)", default="")
                )
                tipo = Prompt.ask("Tipo", default="general")
                marca = _normalizar_opcional(Prompt.ask("Marca (opcional)", default=""))
                await consola.crear_producto(nombre, precio, descripcion, tipo, marca)
            elif opcion == 2:
                await consola.listar_productos()
            elif opcion == 3:
                producto_id = IntPrompt.ask("Id del producto")
                await consola.ver_producto(producto_id)
            elif opcion == 4:
                producto_id = IntPrompt.ask("Id del producto a borrar")
                await consola.borrar_producto(producto_id)
            elif opcion == 5:
                producto_id = IntPrompt.ask("Id del producto a comprar")
                importe_str = Prompt.ask(
                    "Importe (Enter para usar el precio del producto)",
                    default="",
                )
                importe: Decimal | None = None
                if importe_str.strip():
                    importe = Decimal(importe_str)
                await consola.comprar_producto(producto_id, importe)
            elif opcion == 6:
                producto_id = IntPrompt.ask("Id del producto")
                await consola.simular_doble_compra(producto_id)
            elif opcion == 7:
                producto_id = IntPrompt.ask("Id del producto")
                await consola.simular_doble_borrado(producto_id)
            elif opcion == 8:
                await consola.estado_redis()
            elif opcion == 9:
                await consola.estado_bd()
            elif opcion == 10:
                await lanzar_worker()
            elif opcion == 11:
                await consola.inicializar_demo()
            elif opcion == 12:
                await consola.limpiar_cola()
            elif opcion == 13:
                indice = IntPrompt.ask(
                    "Índice a reintentar (-1 para todos)",
                    default=-1,
                )
                await consola.reintentar_dlq(indice)
            elif opcion == 0:
                console.print("[bold cyan]Hasta luego.[/bold cyan]")
                break
            else:
                console.print("[red]Opción no válida.[/red]")
        except Exception as exc:
            console.print(f"[red]Error: {exc}[/red]")

        console.print()


def _construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Cliente de consola para Python+FastAPI Backend."
    )
    sub = parser.add_subparsers(dest="comando", help="comandos disponibles")

    crear = sub.add_parser("crear", help="crear un producto")
    crear.add_argument("--nombre", required=True)
    crear.add_argument("--precio", required=True)
    crear.add_argument("--descripcion")
    crear.add_argument("--tipo", default="general")
    crear.add_argument("--marca")

    sub.add_parser("listar", help="listar productos")

    ver = sub.add_parser("ver", help="ver un producto")
    ver.add_argument("--id", type=int, required=True)

    borrar = sub.add_parser("borrar", help="borrar un producto")
    borrar.add_argument("--id", type=int, required=True)

    comprar = sub.add_parser("comprar", help="comprar un producto")
    comprar.add_argument("--id", type=int, required=True)
    comprar.add_argument("--importe")

    doble_compra = sub.add_parser("doble-compra", help="simular doble compra")
    doble_compra.add_argument("--id", type=int, required=True)

    doble_borrado = sub.add_parser("doble-borrado", help="simular doble borrado")
    doble_borrado.add_argument("--id", type=int, required=True)

    sub.add_parser("redis", help="estado de Redis")
    sub.add_parser("bd", help="estado de la base de datos")
    sub.add_parser("worker", help="lanzar worker")

    seed = sub.add_parser("seed", help="inicializar datos demo")
    seed.add_argument(
        "--force",
        action="store_true",
        help="sobrescribir productos existentes",
    )

    sub.add_parser("limpiar-cola", help="limpiar cola de Redis")

    retry = sub.add_parser("retry-dlq", help="reintentar jobs de la DLQ")
    retry.add_argument(
        "--indice",
        type=int,
        default=-1,
        help="índice de la entrada (-1 para todas)",
    )

    return parser


async def _ejecutar_subcomando(
    args: argparse.Namespace,
    consola: Consola,
) -> None:
    comando = args.comando
    if comando == "crear":
        await consola.crear_producto(
            args.nombre,
            args.precio,
            args.descripcion,
            args.tipo,
            args.marca,
        )
    elif comando == "listar":
        await consola.listar_productos()
    elif comando == "ver":
        await consola.ver_producto(args.id)
    elif comando == "borrar":
        await consola.borrar_producto(args.id)
    elif comando == "comprar":
        importe = Decimal(args.importe) if args.importe else None
        await consola.comprar_producto(args.id, importe)
    elif comando == "doble-compra":
        await consola.simular_doble_compra(args.id)
    elif comando == "doble-borrado":
        await consola.simular_doble_borrado(args.id)
    elif comando == "redis":
        await consola.estado_redis()
    elif comando == "bd":
        await consola.estado_bd()
    elif comando == "worker":
        await lanzar_worker()
    elif comando == "seed":
        await consola.inicializar_demo(forzar=args.force)
    elif comando == "limpiar-cola":
        await consola.limpiar_cola()
    elif comando == "retry-dlq":
        await consola.reintentar_dlq(indice=args.indice)
    else:
        _construir_parser().print_help()


async def main() -> None:
    parser = _construir_parser()
    args = parser.parse_args()

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        consola = Consola(client)
        if args.comando is None:
            await _main_interactivo(consola)
        else:
            await _ejecutar_subcomando(args, consola)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[bold cyan]Saliendo...[/bold cyan]")
        sys.exit(0)
