// Cliente HTTP mínimo hacia api/main.py.
// En desarrollo, Vite hace proxy de /api al backend (ver vite.config.ts).

import { cerrarSesion, obtenerSesion } from './sesion'
import type {
  EntidadImportable,
  ResultadoDeshacerLote,
  ResultadoImportacion,
  SesionUsuario,
} from './tipos'

// Header con el token de sesión guardado localmente, si hay uno (ver
// sesion.ts). Las lecturas (GET) siempre están abiertas; las mutaciones
// (POST/PUT/PATCH/DELETE) exigen este token (ver api/auth.py).
function headersConToken(): HeadersInit {
  const sesion = obtenerSesion()
  return sesion ? { Authorization: `Bearer ${sesion.token}` } : {}
}

async function manejarRespuesta<T>(respuesta: Response): Promise<T> {
  if (!respuesta.ok) {
    // Token vencido o inválido a mitad de sesión: se cierra sola para que
    // la pantalla de login vuelva a aparecer en vez de seguir fallando.
    if (respuesta.status === 401 && obtenerSesion()) {
      cerrarSesion()
    }
    const cuerpo = await respuesta.json().catch(() => null)
    throw new Error(cuerpo?.detail ?? `Error ${respuesta.status}`)
  }
  return respuesta.json()
}

export function obtenerJSON<T>(ruta: string): Promise<T> {
  return fetch(ruta).then((r) => manejarRespuesta<T>(r))
}

export function iniciarSesion(usuario: string, contrasena: string): Promise<SesionUsuario> {
  return fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ usuario, contrasena }),
  }).then((r) => manejarRespuesta<SesionUsuario>(r))
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
    headers: headersConToken(),
  }).then((r) => manejarRespuesta<ResultadoImportacion>(r))
}

export function importarDesdeBD(entidad: EntidadImportable): Promise<ResultadoImportacion> {
  return fetch(`/api/importar-bd/${entidad}`, {
    method: 'POST',
    headers: headersConToken(),
  }).then((r) => manejarRespuesta<ResultadoImportacion>(r))
}

export function deshacerLoteMovimientos(lote: string): Promise<ResultadoDeshacerLote> {
  return fetch(`/api/movimientos/lotes/${encodeURIComponent(lote)}`, {
    method: 'DELETE',
    headers: headersConToken(),
  }).then((r) => manejarRespuesta<ResultadoDeshacerLote>(r))
}

export function formatearLempiras(valor: number): string {
  return `L ${valor.toLocaleString('es-HN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}
