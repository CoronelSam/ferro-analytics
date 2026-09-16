// Envoltorio para los tres estados que repite cada página con datos: carga, error y vacío.

import type { ReactNode } from 'react'

interface Props {
  cargando: boolean
  error: Error | null
  vacio?: boolean
  mensajeVacio?: string
  children: ReactNode
}

export function Estado({ cargando, error, vacio, mensajeVacio = 'Sin datos.', children }: Props) {
  if (cargando) return <p className="text-sm text-neutral-500">Cargando...</p>
  if (error) return <p className="text-sm text-red-600">Error: {error.message}</p>
  if (vacio) return <p className="text-sm text-neutral-500">{mensajeVacio}</p>
  return <>{children}</>
}
