// Paleta categórica fija (6 tonos, orden fijo — nunca reasignada por ranking).
// Cada categoría recibe su slot según el resto de su id entre 6, así el color
// de "Tornillería" es siempre el mismo sin importar qué filtro esté activo.

export const SLOTS = ["cat-1", "cat-2", "cat-3", "cat-4", "cat-5", "cat-6"] as const

export function slotCategoria(idCategoria: number): string {
  const i = ((idCategoria - 1) % SLOTS.length + SLOTS.length) % SLOTS.length
  return SLOTS[i]
}

// Mismos tonos que las variables CSS --cat-N, en hex plano para librerías
// de gráficos (SVG) que no resuelven custom properties de forma fiable.
const HEX: Record<string, string> = {
  'cat-1': '#2a78d6',
  'cat-2': '#eb6834',
  'cat-3': '#1baf7a',
  'cat-4': '#c98500',
  'cat-5': '#d95f8f',
  'cat-6': '#008300',
}

export function hexCategoria(idCategoria: number): string {
  return HEX[slotCategoria(idCategoria)]
}
