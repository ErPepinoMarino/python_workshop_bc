class ProductoNoEncontrado(Exception):
    def __init__(self, producto_id: int) -> None:
        self.producto_id = producto_id
        super().__init__(f"Producto {producto_id} no encontrado")
