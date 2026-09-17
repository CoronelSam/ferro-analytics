// Clave de la API (X-API-Key) para el modo solo lectura opcional del
// backend (ver api/seguridad.py, FERRO_API_KEY). Se guarda solo en este
// navegador (localStorage): nunca se envía a otro sitio que no sea esta
// misma API, y cada persona que comparte el dashboard guarda la suya.

import { useSyncExternalStore } from 'react'

const CLAVE_STORAGE = 'ferro_api_key'

// Pub/sub mínimo para que useClaveApiPresente() se actualice en cualquier
// componente (p. ej. Importar.tsx) apenas se guarda o quita la clave desde
// otro (el control del sidebar), sin pasar por props ni contexto.
type Escucha = () => void
const escuchas = new Set<Escucha>()

function notificar(): void {
  escuchas.forEach((escucha) => escucha())
}

function suscribirse(escucha: Escucha): () => void {
  escuchas.add(escucha)
  return () => escuchas.delete(escucha)
}

export function obtenerClaveApi(): string | null {
  try {
    return localStorage.getItem(CLAVE_STORAGE)
  } catch {
    return null
  }
}

export function guardarClaveApi(clave: string): void {
  try {
    localStorage.setItem(CLAVE_STORAGE, clave)
  } catch {
    // Almacenamiento no disponible (navegación privada, etc.): la clave
    // simplemente no persiste entre recargas, sin romper la página.
  }
  notificar()
}

export function borrarClaveApi(): void {
  try {
    localStorage.removeItem(CLAVE_STORAGE)
  } catch {
    // Ver comentario en guardarClaveApi.
  }
  notificar()
}

/** true si hay una clave guardada en este navegador; se actualiza sola. */
export function useClaveApiPresente(): boolean {
  return useSyncExternalStore(suscribirse, () => obtenerClaveApi() !== null)
}
