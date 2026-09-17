// Paleta categórica fija alineada con la identidad FerroAnalytics.
// Alterna variaciones de azul y naranja sin reasignar colores por ranking.

export const SLOTS = ["cat-1", "cat-2", "cat-3", "cat-4", "cat-5", "cat-6"] as const

export function slotCategoria(idCategoria: number): string {
  const i = ((idCategoria - 1) % SLOTS.length + SLOTS.length) % SLOTS.length
  return SLOTS[i]
}

const HEX: Record<string, string> = {
  'cat-1': '#124E96',
  'cat-2': '#F97316',
  'cat-3': '#2A78D6',
  'cat-4': '#FB923C',
  'cat-5': '#60A5FA',
  'cat-6': '#C2410C',
}

export function hexCategoria(idCategoria: number): string {
  return HEX[slotCategoria(idCategoria)]
}
