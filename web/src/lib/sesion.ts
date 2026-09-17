// Sesión de usuario del dashboard (login, ver api/auth.py y
// api/rutas/auth.py). El token y el perfil se guardan solo en este
// navegador (localStorage): cada persona que usa el dashboard inicia
// sesión con su propio usuario.

import { useSyncExternalStore } from 'react'
import type { SesionUsuario } from './tipos'

const SESION_STORAGE = 'ferro_sesion'

// Pub/sub mínimo para que useSesion() se actualice en cualquier componente
// apenas se guarda o se quita la sesión desde otro (login, cerrar sesión,
// o un 401 de la API), sin pasar por props ni contexto.
type Escucha = () => void
const escuchas = new Set<Escucha>()

function notificar(): void {
  escuchas.forEach((escucha) => escucha())
}

function suscribirse(escucha: Escucha): () => void {
  escuchas.add(escucha)
  return () => escuchas.delete(escucha)
}

function leerDesdeStorage(): SesionUsuario | null {
  try {
    const guardada = localStorage.getItem(SESION_STORAGE)
    return guardada ? (JSON.parse(guardada) as SesionUsuario) : null
  } catch {
    return null
  }
}

// useSyncExternalStore exige que getSnapshot devuelva la misma referencia
// mientras no haya cambios; JSON.parse crea un objeto nuevo en cada
// llamada, lo que provoca un loop infinito de renders. Se cachea acá y
// solo se reemplaza cuando la sesión realmente cambia.
let cache: SesionUsuario | null = leerDesdeStorage()

export function obtenerSesion(): SesionUsuario | null {
  return cache
}

export function guardarSesion(sesion: SesionUsuario): void {
  cache = sesion
  try {
    localStorage.setItem(SESION_STORAGE, JSON.stringify(sesion))
  } catch {
    // Almacenamiento no disponible (navegación privada, etc.): la sesión
    // simplemente no persiste entre recargas, sin romper la página.
  }
  notificar()
}

export function cerrarSesion(): void {
  cache = null
  try {
    localStorage.removeItem(SESION_STORAGE)
  } catch {
    // Ver comentario en guardarSesion.
  }
  notificar()
}

/** Sesión activa en este navegador, o null; se actualiza sola. */
export function useSesion(): SesionUsuario | null {
  return useSyncExternalStore(suscribirse, obtenerSesion)
}
