# pedido id es el id de la tabla
# operacion e si es cobro, devolucion...
# version es si se paga con una tarjeta, otra, en efectivo..
# todo junto es lo que denominamos idempotency_key
def order_id(pedido_id: str, operacion: str, version: int = 1) -> str:
    return f"{pedido_id}:{operacion}:v{version}"
