"""
Esquemas Pydantic para la API de FerroAnalytics.
Definen la forma de los datos que entran y salen por HTTP; no contienen
lógica de negocio, solo mapean los modelos y dicts que ya produce src/.
"""

from pydantic import BaseModel


# ──────────────────────────────────────────────
# Entidades base
# ──────────────────────────────────────────────

class Producto(BaseModel):
    codigo: str
    nombre: str
    id_categoria: int
    precio_unitario: float
    stock_actual: int
    stock_minimo: int
    fecha_ultima_actualizacion: str


class Categoria(BaseModel):
    id: int
    nombre: str


class Movimiento(BaseModel):
    id_movimiento: int
    codigo_producto: str
    tipo: str
    cantidad: int
    fecha: str
    lote_origen: str


# ──────────────────────────────────────────────
# Reportes (Reporte 1-4 de src/reportes.py)
# ──────────────────────────────────────────────

class StockPorCategoria(BaseModel):
    id_categoria: int
    nombre: str
    num_productos: int
    stock_total: int
    valor_total: float


class ProductoInmovilizado(BaseModel):
    codigo: str
    nombre: str
    id_categoria: int
    stock_actual: int
    precio_unitario: float
    valor_inmovilizado: float
    ultima_salida: str | None


class VentaMensualCategoria(BaseModel):
    anio: int
    mes: int
    id_categoria: int
    nombre_categoria: str
    unidades: int


class AlertaStockBajo(BaseModel):
    codigo: str
    nombre: str
    id_categoria: int
    stock_actual: int
    minimo: int
    diferencia: int


# ──────────────────────────────────────────────
# Importación
# ──────────────────────────────────────────────

class FilaRechazada(BaseModel):
    fila: int
    datos: dict
    motivo: str


class ResultadoImportacion(BaseModel):
    entidad: str
    aceptados: int
    rechazados: list[FilaRechazada]
    insertados: int | None = None
    actualizados: int | None = None
