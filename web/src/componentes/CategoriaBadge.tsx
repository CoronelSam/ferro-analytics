import { slotCategoria } from '../lib/colores'

export function CategoriaBadge({ idCategoria, nombre }: { idCategoria: number; nombre: string }) {
  const slot = slotCategoria(idCategoria)
  return (
    <span
      className="inline-flex items-center gap-1.5 whitespace-nowrap rounded-full border border-white/60 py-1 pl-1.5 pr-2.5 text-[11.5px] font-extrabold text-[#43566F] shadow-[inset_0_0_0_1px_rgba(19,35,58,0.035)]"
      style={{ background: `var(--${slot}-t)` }}
    >
      <span className="h-1.5 w-1.5 rounded-full" style={{ background: `var(--${slot})` }} />
      {nombre}
    </span>
  )
}
