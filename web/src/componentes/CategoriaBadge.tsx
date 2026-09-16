import { slotCategoria } from '../lib/colores'

export function CategoriaBadge({ idCategoria, nombre }: { idCategoria: number; nombre: string }) {
  const slot = slotCategoria(idCategoria)
  return (
    <span
      className="inline-flex items-center gap-1.5 whitespace-nowrap rounded-full py-1 pl-1.5 pr-2.5 text-xs font-bold text-neutral-700"
      style={{ background: `var(--${slot}-t)` }}
    >
      <span className="h-1.5 w-1.5 rounded-full" style={{ background: `var(--${slot})` }} />
      {nombre}
    </span>
  )
}
