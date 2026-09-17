// Hook de paginación en cliente para listas ya cargadas por completo (arreglos en memoria).

import { useMemo, useState } from 'react'

export function usePaginacion<T>(items: T[], porPagina: number) {
  const [pagina, setPagina] = useState(1)
  const totalPaginas = Math.max(1, Math.ceil(items.length / porPagina))
  const paginaActual = Math.min(pagina, totalPaginas)

  const itemsPagina = useMemo(
    () => items.slice((paginaActual - 1) * porPagina, paginaActual * porPagina),
    [items, paginaActual, porPagina],
  )

  return {
    pagina: paginaActual,
    totalPaginas,
    total: items.length,
    porPagina,
    items: itemsPagina,
    irA: (p: number) => setPagina(Math.min(Math.max(1, p), totalPaginas)),
    reiniciar: () => setPagina(1),
  }
}
