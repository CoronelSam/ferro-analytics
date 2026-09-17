import type { ReactNode } from 'react'
import { IconoAlerta, IconoInventario } from './Icono'
import { Skeleton } from './Skeleton'

interface Props {
  cargando: boolean
  error: Error | null
  vacio?: boolean
  mensajeVacio?: string
  children: ReactNode
}

export function Estado({ cargando, error, vacio, mensajeVacio = 'Sin datos disponibles.', children }: Props) {
  if (cargando) {
    return (
      <div className="flex flex-col gap-3 py-3" aria-label="Cargando información">
        <Skeleton className="h-4 w-2/5" />
        <Skeleton className="h-3 w-full" />
        <Skeleton className="h-3 w-4/5" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-start gap-3 rounded-xl border border-red-100 bg-red-50/70 px-4 py-3.5 text-red-700">
        <span className="mt-0.5 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-white/80">
          <IconoAlerta size={17} />
        </span>
        <div>
          <div className="text-[13px] font-extrabold">No se pudo cargar la información</div>
          <div className="mt-0.5 text-xs font-semibold opacity-80">{error.message}</div>
        </div>
      </div>
    )
  }

  if (vacio) {
    return (
      <div className="flex min-h-32 flex-col items-center justify-center rounded-xl border border-dashed border-[#C9D7E6] bg-[#F8FAFD] px-5 py-7 text-center">
        <span className="mb-2.5 flex h-10 w-10 items-center justify-center rounded-xl bg-[#EAF2FC] text-[#124E96]">
          <IconoInventario size={20} />
        </span>
        <p className="max-w-md text-[13px] font-bold text-[#6D7B8F]">{mensajeVacio}</p>
      </div>
    )
  }

  return <>{children}</>
}
