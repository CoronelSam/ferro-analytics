// Cliente HTTP mínimo hacia api/main.py.
// En desarrollo, Vite hace proxy de /api al backend (ver vite.config.ts).

import type { EntidadImportable, ResultadoImportacion } from './tipos'

async function manejarRespuesta<T>(respuesta: Response): Promise<T> {
  if (!respuesta.ok) {
    const cuerpo = await respuesta.json().catch(() => null)
    throw new Error(cuerpo?.detail ?? `Error ${respuesta.status}`)
  }
  return respuesta.json()
}

export function obtenerJSON<T>(ruta: string): Promise<T> {
  return fetch(ruta).then((r) => manejarRespuesta<T>(r))
}

export function importarCSV(
  entidad: EntidadImportable,
  archivo: File,
): Promise<ResultadoImportacion> {
  const form = new FormData()
  form.append('archivo', archivo)
  return fetch(`/api/importar/${entidad}`, { method: 'POST', body: form }).then(
    (r) => manejarRespuesta<ResultadoImportacion>(r),
  )
}

export function importarDesdeBD(entidad: EntidadImportable): Promise<ResultadoImportacion> {
  return fetch(`/api/importar-bd/${entidad}`, { method: 'POST' }).then(
    (r) => manejarRespuesta<ResultadoImportacion>(r),
  )
}

export function formatearLempiras(valor: number): string {
  return `L ${valor.toLocaleString('es-HN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}
