// Hooks de TanStack Query, uno por endpoint de la API.

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { deshacerLoteMovimientos, importarCSV, importarDesdeBD, iniciarSesion, obtenerJSON } from './api'
import { guardarSesion } from './sesion'
import type {
  AlertaStockBajo,
  CeldaResumen,
  Categoria,
  ClasificacionABCXYZ,
  EntidadImportable,
  EstadoImportacionBD,
  LoteMovimientos,
  MigracionCelda,
  Movimiento,
  Producto,
  ProductoInmovilizado,
  PronosticoCategoria,
  PronosticoProducto,
  Salud,
  StockPorCategoria,
  VentaMensualCategoria,
} from './tipos'

export function useSalud() {
  return useQuery({
    queryKey: ['salud'],
    queryFn: () => obtenerJSON<Salud>('/api/salud'),
    staleTime: 60_000,
  })
}

export function useIniciarSesion() {
  return useMutation({
    mutationFn: ({ usuario, contrasena }: { usuario: string; contrasena: string }) =>
      iniciarSesion(usuario, contrasena),
    onSuccess: (sesion) => guardarSesion(sesion),
  })
}

export function useProductos() {
  return useQuery({
    queryKey: ['productos'],
    queryFn: () => obtenerJSON<Producto[]>('/api/productos'),
  })
}

export function useCategorias() {
  return useQuery({
    queryKey: ['categorias'],
    queryFn: () => obtenerJSON<Categoria[]>('/api/categorias'),
  })
}

export interface FiltrosMovimientos {
  fechaDesde?: string
  fechaHasta?: string
  tipo?: 'E' | 'S'
}

export function useMovimientos(filtros: FiltrosMovimientos) {
  const parametros = new URLSearchParams()
  if (filtros.fechaDesde) parametros.set('fecha_desde', filtros.fechaDesde)
  if (filtros.fechaHasta) parametros.set('fecha_hasta', filtros.fechaHasta)
  if (filtros.tipo) parametros.set('tipo', filtros.tipo)

  return useQuery({
    queryKey: ['movimientos', filtros],
    queryFn: () => obtenerJSON<Movimiento[]>(`/api/movimientos?${parametros}`),
  })
}

export function useStockPorCategoria() {
  return useQuery({
    queryKey: ['reportes', 'stock-por-categoria'],
    queryFn: () => obtenerJSON<StockPorCategoria[]>('/api/reportes/stock-por-categoria'),
  })
}

export function useTopInmovilizado(n: number, dias: number) {
  return useQuery({
    queryKey: ['reportes', 'top-inmovilizado', n, dias],
    queryFn: () =>
      obtenerJSON<ProductoInmovilizado[]>(
        `/api/reportes/top-inmovilizado?n=${n}&dias=${dias}`,
      ),
  })
}

export function useVentasMensuales() {
  return useQuery({
    queryKey: ['reportes', 'ventas-mensuales'],
    queryFn: () =>
      obtenerJSON<VentaMensualCategoria[]>('/api/reportes/ventas-mensuales'),
  })
}

export function useAlertas(umbral: number | null) {
  const sufijo = umbral !== null ? `?umbral=${umbral}` : ''
  return useQuery({
    queryKey: ['reportes', 'alertas', umbral],
    queryFn: () => obtenerJSON<AlertaStockBajo[]>(`/api/reportes/alertas${sufijo}`),
  })
}

export function useImportaciones() {
  return useQuery({
    queryKey: ['importaciones'],
    queryFn: () => obtenerJSON<string[]>('/api/importaciones'),
  })
}

export function useClasificacionABCXYZ() {
  return useQuery({
    queryKey: ['analitica', 'abc-xyz'],
    queryFn: () => obtenerJSON<ClasificacionABCXYZ[]>('/api/analitica/abc-xyz'),
  })
}

export function useResumenABCXYZ() {
  return useQuery({
    queryKey: ['analitica', 'abc-xyz', 'resumen'],
    queryFn: () => obtenerJSON<CeldaResumen[]>('/api/analitica/abc-xyz/resumen'),
  })
}

export function useProductosPrioritarios() {
  return useQuery({
    queryKey: ['analitica', 'prediccion', 'productos-prioritarios'],
    queryFn: () => obtenerJSON<string[]>('/api/analitica/prediccion/productos-prioritarios'),
  })
}

/** Pronóstico de todos los productos A/X en una sola llamada (ver /prediccion/lote). */
export function usePronosticoLote(opciones: OpcionesPronostico = {}) {
  const parametros = new URLSearchParams()
  if (opciones.n) parametros.set('n', String(opciones.n))
  if (opciones.nPrueba) parametros.set('n_prueba', String(opciones.nPrueba))

  return useQuery({
    queryKey: ['analitica', 'prediccion', 'lote', opciones],
    queryFn: () => obtenerJSON<PronosticoProducto[]>(`/api/analitica/prediccion/lote?${parametros}`),
  })
}

export function useMigracionesABCXYZ(ventanaMeses = 12) {
  return useQuery({
    queryKey: ['analitica', 'abc-xyz', 'migraciones', ventanaMeses],
    queryFn: () =>
      obtenerJSON<MigracionCelda[]>(
        `/api/analitica/abc-xyz/migraciones?ventana_meses=${ventanaMeses}`,
      ),
  })
}

export interface OpcionesPronostico {
  n?: number
  nPrueba?: number
}

export function usePronosticoCategoria(idCategoria: number | null, opciones: OpcionesPronostico = {}) {
  const parametros = new URLSearchParams()
  if (opciones.n) parametros.set('n', String(opciones.n))
  if (opciones.nPrueba) parametros.set('n_prueba', String(opciones.nPrueba))

  return useQuery({
    queryKey: ['analitica', 'prediccion', 'categoria', idCategoria, opciones],
    queryFn: () =>
      obtenerJSON<PronosticoCategoria>(
        `/api/analitica/prediccion/categoria/${idCategoria}?${parametros}`,
      ),
    enabled: idCategoria !== null,
  })
}

export interface OpcionesPronosticoProducto extends OpcionesPronostico {
  tiempoEntregaDias?: number
  nivelServicio?: number
}

export function usePronosticoProducto(codigo: string | null, opciones: OpcionesPronosticoProducto = {}) {
  const parametros = new URLSearchParams()
  if (opciones.n) parametros.set('n', String(opciones.n))
  if (opciones.nPrueba) parametros.set('n_prueba', String(opciones.nPrueba))
  if (opciones.tiempoEntregaDias) parametros.set('tiempo_entrega_dias', String(opciones.tiempoEntregaDias))
  if (opciones.nivelServicio) parametros.set('nivel_servicio', String(opciones.nivelServicio))

  return useQuery({
    queryKey: ['analitica', 'prediccion', 'producto', codigo, opciones],
    queryFn: () =>
      obtenerJSON<PronosticoProducto>(
        `/api/analitica/prediccion/producto/${codigo}?${parametros}`,
      ),
    enabled: codigo !== null,
  })
}

export function useImportarCSV() {
  const cliente = useQueryClient()
  return useMutation({
    mutationFn: ({ entidad, archivo }: { entidad: EntidadImportable; archivo: File }) =>
      importarCSV(entidad, archivo),
    onSuccess: () => {
      // Los datos en el backend cambiaron; invalida todo lo que depende de ellos.
      cliente.invalidateQueries()
    },
  })
}

export function useEstadoImportacionBD() {
  return useQuery({
    queryKey: ['importar-bd', 'estado'],
    queryFn: () => obtenerJSON<EstadoImportacionBD>('/api/importar-bd/estado'),
  })
}

export function useImportarDesdeBD() {
  const cliente = useQueryClient()
  return useMutation({
    mutationFn: (entidad: EntidadImportable) => importarDesdeBD(entidad),
    onSuccess: () => {
      cliente.invalidateQueries()
    },
  })
}

export function useLotesMovimientos() {
  return useQuery({
    queryKey: ['movimientos', 'lotes'],
    queryFn: () => obtenerJSON<LoteMovimientos[]>('/api/movimientos/lotes'),
  })
}

export function useDeshacerLoteMovimientos() {
  const cliente = useQueryClient()
  return useMutation({
    mutationFn: (lote: string) => deshacerLoteMovimientos(lote),
    onSuccess: () => {
      cliente.invalidateQueries()
    },
  })
}
