"""
Modelos de datos para FerroAnalytics (Fase I).
Define las clases de datos y sus formatos struct para almacenamiento binario.
"""

import struct
from datetime import datetime, date


# Prefijo '<' = little-endian sin padding entre campos
# Formato binario: 10s 40s i f i i 10s → 76 bytes
FORMATO_PRODUCTO = "<10s40sifii10s"
TAMANO_PRODUCTO = struct.calcsize(FORMATO_PRODUCTO)

# Formato binario: i 30s → 34 bytes
FORMATO_CATEGORIA = "<i30s"
TAMANO_CATEGORIA = struct.calcsize(FORMATO_CATEGORIA)

# Formato binario: i 10s 1s i 10s 40s → 69 bytes
FORMATO_MOVIMIENTO = "<i10s1si10s40s"
TAMANO_MOVIMIENTO = struct.calcsize(FORMATO_MOVIMIENTO)

# Formato para registro de importaciones: 60s (nombre del archivo)
FORMATO_IMPORTACION = "60s"
TAMANO_IMPORTACION = struct.calcsize(FORMATO_IMPORTACION)


class ProductoAnalitico:
    """
    Representa un producto del inventario para análisis.

    Atributos:
        codigo (str): Código único del producto (máx. 10 caracteres).
        nombre (str): Nombre descriptivo del producto (máx. 40 caracteres).
        id_categoria (int): Identificador de la categoría a la que pertenece.
        precio_unitario (float): Precio por unidad. Debe ser >= 0.
        stock_actual (int): Unidades disponibles actualmente. Debe ser >= 0.
        stock_minimo (int): Umbral mínimo de stock aceptable. Debe ser >= 0.
        fecha_ultima_actualizacion (str): Fecha de la última modificación (AAAA-MM-DD).
    """

    def __init__(self, codigo: str, nombre: str, id_categoria: int,
                 precio_unitario: float, stock_actual: int,
                 stock_minimo: int, fecha_ultima_actualizacion: str = ""):
        self.codigo = codigo[:10]
        self.nombre = nombre[:40]
        self.id_categoria = id_categoria
        self.precio_unitario = precio_unitario
        self.stock_actual = stock_actual
        self.stock_minimo = stock_minimo
        self.fecha_ultima_actualizacion = (
            fecha_ultima_actualizacion
            if fecha_ultima_actualizacion
            else date.today().isoformat()
        )

    def a_bytes(self) -> bytes:
        """Serializa el registro a bytes usando el formato struct definido."""
        return struct.pack(
            FORMATO_PRODUCTO,
            self.codigo.encode("utf-8").ljust(10)[:10],
            self.nombre.encode("utf-8").ljust(40)[:40],
            self.id_categoria,
            self.precio_unitario,
            self.stock_actual,
            self.stock_minimo,
            self.fecha_ultima_actualizacion.encode("utf-8").ljust(10)[:10],
        )

    @classmethod
    def desde_bytes(cls, datos: bytes) -> "ProductoAnalitico":
        """Deserializa un registro desde bytes leídos del archivo binario."""
        campos = struct.unpack(FORMATO_PRODUCTO, datos)
        return cls(
            codigo=campos[0].decode("utf-8").rstrip("\x00").strip(),
            nombre=campos[1].decode("utf-8").rstrip("\x00").strip(),
            id_categoria=campos[2],
            precio_unitario=campos[3],
            stock_actual=campos[4],
            stock_minimo=campos[5],
            fecha_ultima_actualizacion=campos[6].decode("utf-8").rstrip("\x00").strip(),
        )

    def __repr__(self) -> str:
        return (
            f"ProductoAnalitico(codigo={self.codigo!r}, nombre={self.nombre!r}, "
            f"id_categoria={self.id_categoria}, precio_unitario={self.precio_unitario}, "
            f"stock_actual={self.stock_actual}, stock_minimo={self.stock_minimo}, "
            f"fecha_ultima_actualizacion={self.fecha_ultima_actualizacion!r})"
        )


class CategoriaAnalitica:
    """
    Representa una categoría de productos.

    Atributos:
        id (int): Identificador único de la categoría.
        nombre (str): Nombre de la categoría (máx. 30 caracteres).
    """

    def __init__(self, id: int, nombre: str):
        self.id = id
        self.nombre = nombre[:30]

    def a_bytes(self) -> bytes:
        """Serializa el registro a bytes usando el formato struct definido."""
        return struct.pack(
            FORMATO_CATEGORIA,
            self.id,
            self.nombre.encode("utf-8").ljust(30)[:30],
        )

    @classmethod
    def desde_bytes(cls, datos: bytes) -> "CategoriaAnalitica":
        """Deserializa un registro desde bytes leídos del archivo binario."""
        campos = struct.unpack(FORMATO_CATEGORIA, datos)
        return cls(
            id=campos[0],
            nombre=campos[1].decode("utf-8").rstrip("\x00").strip(),
        )

    def __repr__(self) -> str:
        return f"CategoriaAnalitica(id={self.id}, nombre={self.nombre!r})"


class MovimientoAnalitico:
    """
    Representa un movimiento de inventario (entrada o salida).

    Atributos:
        id_movimiento (int): Identificador único del movimiento.
        codigo_producto (str): Código del producto involucrado (máx. 10 caracteres).
        tipo (str): 'E' para entrada, 'S' para salida.
        cantidad (int): Unidades del movimiento. Debe ser >= 0.
        fecha (str): Fecha del movimiento en formato AAAA-MM-DD.
        lote_origen (str): Referencia al lote de origen (máx. 40 caracteres).
    """

    TIPOS_VALIDOS = {"E", "S"}

    def __init__(self, id_movimiento: int, codigo_producto: str, tipo: str,
                 cantidad: int, fecha: str, lote_origen: str = ""):
        self.id_movimiento = id_movimiento
        self.codigo_producto = codigo_producto[:10]
        self.tipo = tipo.upper()
        self.cantidad = cantidad
        self.fecha = fecha
        self.lote_origen = lote_origen[:40]

    def a_bytes(self) -> bytes:
        """Serializa el registro a bytes usando el formato struct definido."""
        return struct.pack(
            FORMATO_MOVIMIENTO,
            self.id_movimiento,
            self.codigo_producto.encode("utf-8").ljust(10)[:10],
            self.tipo.encode("utf-8").ljust(1)[:1],
            self.cantidad,
            self.fecha.encode("utf-8").ljust(10)[:10],
            self.lote_origen.encode("utf-8").ljust(40)[:40],
        )

    @classmethod
    def desde_bytes(cls, datos: bytes) -> "MovimientoAnalitico":
        """Deserializa un registro desde bytes leídos del archivo binario."""
        campos = struct.unpack(FORMATO_MOVIMIENTO, datos)
        return cls(
            id_movimiento=campos[0],
            codigo_producto=campos[1].decode("utf-8").rstrip("\x00").strip(),
            tipo=campos[2].decode("utf-8").rstrip("\x00").strip(),
            cantidad=campos[3],
            fecha=campos[4].decode("utf-8").rstrip("\x00").strip(),
            lote_origen=campos[5].decode("utf-8").rstrip("\x00").strip(),
        )

    def __repr__(self) -> str:
        return (
            f"MovimientoAnalitico(id_movimiento={self.id_movimiento}, "
            f"codigo_producto={self.codigo_producto!r}, tipo={self.tipo!r}, "
            f"cantidad={self.cantidad}, fecha={self.fecha!r}, "
            f"lote_origen={self.lote_origen!r})"
        )
