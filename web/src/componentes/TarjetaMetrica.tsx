import type { ReactElement } from 'react'

export function TarjetaMetrica({
  etiqueta,
  valor,
  caption,
  Icono,
  tono = 'azul',
}: {
  etiqueta: string
  valor: string
  caption: string
  Icono: (p: { size?: number; className?: string }) => ReactElement
  tono?: 'azul' | 'naranja' | 'alerta'
}) {
  const estilos = {
    azul: { icono: 'bg-[#EAF2FC] text-[#124E96]', valor: 'text-[#13233A]', borde: 'border-[#DCE5EF]' },
    naranja: { icono: 'bg-[#FFF1E7] text-[#E65F00]', valor: 'text-[#13233A]', borde: 'border-[#F0DDCF]' },
    alerta: { icono: 'bg-[#FFF1E7] text-[#E65F00]', valor: 'text-[#E65F00]', borde: 'border-[#FFD7BC]' },
  }[tono]

  return (
    <div className={`fa-card fa-card-interactive flex min-w-0 flex-1 flex-col gap-3 border ${estilos.borde} p-5`}>
      <div className="flex items-center justify-between gap-3">
        <span className="truncate text-[10.5px] font-extrabold uppercase tracking-[0.08em] text-[#6D7B8F]">{etiqueta}</span>
        <span className={`flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-xl ${estilos.icono}`}>
          <Icono size={17} />
        </span>
      </div>
      <span className={`truncate text-[27px] font-extrabold tracking-[-0.03em] ${estilos.valor}`}>{valor}</span>
      <span className="truncate text-xs font-semibold text-[#6D7B8F]">{caption}</span>
    </div>
  )
}
