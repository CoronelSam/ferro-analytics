// Cliente HTTP mínimo hacia api/main.py.
// En desarrollo, Vite hace proxy de /api al backend (ver vite.config.ts).

import { obtenerClaveApi } from './claveApi'
import type { EntidadImportable, ResultadoDeshacerLote, ResultadoImportacion } from './tipos'

// Header con la clave guardada localmente, si hay una (ver claveApi.ts).
// Sin FERRO_API_KEY configurada en el servidor, el backend la ignora; con
// ella configurada, la exige solo en mutaciones (POST/PUT/PATCH/DELETE).
function headersConClave(): HeadersInit {
  const clave = obtenerClaveApi()
  return clave ? { 'X-API-Key': clave } : {}
}

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
  return fetch(`/api/importar/${entidad}`, {
    method: 'POST',
    body: form,
    headers: headersConClave(),
  }).then((r) => manejarRespuesta<ResultadoImportacion>(r))
}

export function importarDesdeBD(entidad: EntidadImportable): Promise<ResultadoImportacion> {
  return fetch(`/api/importar-bd/${entidad}`, {
    method: 'POST',
    headers: headersConClave(),
  }).then((r) => manejarRespuesta<ResultadoImportacion>(r))
}

export function deshacerLoteMovimientos(lote: string): Promise<ResultadoDeshacerLote> {
  return fetch(`/api/movimientos/lotes/${encodeURIComponent(lote)}`, {
    method: 'DELETE',
    headers: headersConClave(),
  }).then((r) => manejarRespuesta<ResultadoDeshacerLote>(r))
}

export function formatearLempiras(valor: number): string {
  return `L ${valor.toLocaleString('es-HN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}
