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
# Autenticación (ver api/usuarios.py, api/auth.py)
# ──────────────────────────────────────────────

class SolicitudLogin(BaseModel):
    usuario: str
    contrasena: str


class SesionUsuario(BaseModel):
    token: str
    usuario: str
    nombre: str
    rol: str


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
    lote: str | None = None


class EstadoImportacionBD(BaseModel):
    disponible: bool
    motor: str | None
    detalle: str | None


class LoteMovimientos(BaseModel):
    lote: str
    cantidad: int
    fecha_desde: str
    fecha_hasta: str


class ResultadoDeshacerLote(BaseModel):
    lote: str
    eliminados: int


# ──────────────────────────────────────────────
# Analítica: clasificación ABC-XYZ (src/clasificacion.py)
# ──────────────────────────────────────────────

class ClasificacionABCXYZ(BaseModel):
    codigo: str
    nombre: str
    valor_consumo: float
    clase_abc: str
    cv_demanda: float | None
    clase_xyz: str
    celda: str
    recomendacion: str


class CeldaResumen(BaseModel):
    celda: str
    clase_abc: str
    clase_xyz: str
    num_productos: int
    valor_consumo_total: float
    recomendacion: str


class MigracionCelda(BaseModel):
    mes: str
    codigo: str
    nombre: str
    celda_anterior: str
    celda_nueva: str


# ──────────────────────────────────────────────
# Analítica: predicción de demanda (src/prediccion.py)
# ──────────────────────────────────────────────

class ComparacionModelo(BaseModel):
    modelo: str
    mae: float
    mape: float | None
    mase: float | None


class IntervaloConfianza(BaseModel):
    limite_inferior: float
    limite_superior: float


class PuntoMensual(BaseModel):
    mes: str
    unidades: int


class PronosticoCategoria(BaseModel):
    id_categoria: int
    nombre_categoria: str
    meses_pronosticados: list[str]
    comparacion_modelos: list[ComparacionModelo]
    mejor_modelo: str
    pronostico: list[float]
    intervalo_confianza: list[IntervaloConfianza]
    serie_historica: list[PuntoMensual]


class PronosticoProducto(BaseModel):
    codigo: str
    meses_pronosticados: list[str]
    comparacion_modelos: list[ComparacionModelo]
    mejor_modelo: str
    pronostico: list[float]
    intervalo_confianza: list[IntervaloConfianza]
    serie_historica: list[PuntoMensual]
    demanda_diaria_media: float
    demanda_diaria_desviacion: float
    z: float
    stock_seguridad: float
    punto_reorden: float
