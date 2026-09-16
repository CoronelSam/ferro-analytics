// Hooks de TanStack Query, uno por endpoint de la API.

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { importarCSV, obtenerJSON } from './api'
import type {
  AlertaStockBajo,
  Categoria,
  EntidadImportable,
  Movimiento,
  Producto,
  ProductoInmovilizado,
  StockPorCategoria,
  VentaMensualCategoria,
} from './tipos'

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
