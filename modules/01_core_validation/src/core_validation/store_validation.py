from core_validation.product import Producto


def validar_producto_para_tienda(
    producto: Producto,
    categorias_permitidas: set[str],
) -> None:
    """Raise ValueError if the product category is not allowed by the store."""
    if producto.tipo not in categorias_permitidas:
        raise ValueError(
            f"La categoría {producto.tipo!r} no está permitida en esta tienda"
        )
