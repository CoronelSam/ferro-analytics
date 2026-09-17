// Tipos que reflejan los esquemas de api/esquemas.py.
// Mantener sincronizados a mano: son pocos y cambian junto con el backend.

export interface Producto {
  codigo: string
  nombre: string
  id_categoria: number
  precio_unitario: number
  stock_actual: number
  stock_minimo: number
  fecha_ultima_actualizacion: string
}

export interface Categoria {
  id: number
  nombre: string
}

export interface Movimiento {
  id_movimiento: number
  codigo_producto: string
  tipo: 'E' | 'S'
  cantidad: number
  fecha: string
  lote_origen: string
}

export interface StockPorCategoria {
  id_categoria: number
  nombre: string
  num_productos: number
  stock_total: number
  valor_total: number
}

export interface ProductoInmovilizado {
  codigo: string
  nombre: string
  id_categoria: number
  stock_actual: number
  precio_unitario: number
  valor_inmovilizado: number
  ultima_salida: string | null
}

export interface VentaMensualCategoria {
  anio: number
  mes: number
  id_categoria: number
  nombre_categoria: string
  unidades: number
}

export interface AlertaStockBajo {
  codigo: string
  nombre: string
  id_categoria: number
  stock_actual: number
  minimo: number
  diferencia: number
}

export interface FilaRechazada {
  fila: number
  datos: Record<string, string>
  motivo: string
}

export interface ResultadoImportacion {
  entidad: string
  aceptados: number
  rechazados: FilaRechazada[]
  insertados: number | null
  actualizados: number | null
  lote?: string | null
}

export type EntidadImportable = 'categorias' | 'productos' | 'movimientos'

export interface LoteMovimientos {
  lote: string
  cantidad: number
  fecha_desde: string
  fecha_hasta: string
}

export interface ResultadoDeshacerLote {
  lote: string
  eliminados: number
}

export interface EstadoImportacionBD {
  disponible: boolean
  motor: string | null
  detalle: string | null
}

export interface Salud {
  estado: string
}

// ──────────────────────────────────────────────
// Autenticación (ver api/usuarios.py, api/auth.py)
// ──────────────────────────────────────────────

export interface SesionUsuario {
  token: string
  usuario: string
  nombre: string
  rol: string
}

// ──────────────────────────────────────────────
// Analítica: clasificación ABC-XYZ y predicción de demanda
// ──────────────────────────────────────────────

export type ClaseABC = 'A' | 'B' | 'C'
export type ClaseXYZ = 'X' | 'Y' | 'Z'

export interface ClasificacionABCXYZ {
  codigo: string
  nombre: string
  valor_consumo: number
  clase_abc: ClaseABC
  cv_demanda: number | null
  clase_xyz: ClaseXYZ
  celda: string
  recomendacion: string
}

export interface CeldaResumen {
  celda: string
  clase_abc: ClaseABC
  clase_xyz: ClaseXYZ
  num_productos: number
  valor_consumo_total: number
  recomendacion: string
}

export interface MigracionCelda {
  mes: string
  codigo: string
  nombre: string
  celda_anterior: string
  celda_nueva: string
}

export interface ComparacionModelo {
  modelo: 'ingenuo' | 'media_movil' | 'suavizado_exponencial' | 'naive_estacional' | 'regresion'
  mae: number
  mape: number | null
  mase: number | null
}

export interface IntervaloConfianza {
  limite_inferior: number
  limite_superior: number
}

export interface PuntoMensual {
  mes: string
  unidades: number
}

export interface PronosticoCategoria {
  id_categoria: number
  nombre_categoria: string
  meses_pronosticados: string[]
  comparacion_modelos: ComparacionModelo[]
  mejor_modelo: string
  pronostico: number[]
  intervalo_confianza: IntervaloConfianza[]
  serie_historica: PuntoMensual[]
}

export interface PronosticoProducto {
  codigo: string
  meses_pronosticados: string[]
  comparacion_modelos: ComparacionModelo[]
  mejor_modelo: string
  pronostico: number[]
  intervalo_confianza: IntervaloConfianza[]
  serie_historica: PuntoMensual[]
  demanda_diaria_media: number
  demanda_diaria_desviacion: number
  z: number
  stock_seguridad: number
  punto_reorden: number
}
