import { IconoChevronAbajo } from './Icono'

interface Props {
  pagina: number
  totalPaginas: number
  total: number
  porPagina: number
  onIrA: (pagina: number) => void
}

export function Paginador({ pagina, totalPaginas, total, porPagina, onIrA }: Props) {
  const desde = total === 0 ? 0 : (pagina - 1) * porPagina + 1
  const hasta = Math.min(pagina * porPagina, total)

  return (
    <div className="flex items-center justify-between border-t border-[#E8EEF5] bg-[#FAFBFD] px-4 py-3 text-xs font-semibold text-[#6D7B8F]">
      <span>
        Mostrando {desde}–{hasta} de {total}
      </span>
      {totalPaginas > 1 && (
        <div className="flex items-center gap-1.5">
          <button
            onClick={() => onIrA(pagina - 1)}
            disabled={pagina <= 1}
            className="flex h-7 w-7 items-center justify-center rounded-lg border border-[#DCE5EF] bg-white text-[#43566F] rotate-90 hover:border-[#AFC3DA] hover:bg-[#F8FBFF] disabled:opacity-35 disabled:hover:border-[#DCE5EF] disabled:hover:bg-white"
            aria-label="Página anterior"
          >
            <IconoChevronAbajo size={13} />
          </button>
          <span className="px-1.5 font-bold text-[#43566F]">
            Página {pagina} de {totalPaginas}
          </span>
          <button
            onClick={() => onIrA(pagina + 1)}
            disabled={pagina >= totalPaginas}
            className="flex h-7 w-7 items-center justify-center rounded-lg border border-[#DCE5EF] bg-white text-[#43566F] -rotate-90 hover:border-[#AFC3DA] hover:bg-[#F8FBFF] disabled:opacity-35 disabled:hover:border-[#DCE5EF] disabled:hover:bg-white"
            aria-label="Página siguiente"
          >
            <IconoChevronAbajo size={13} />
          </button>
        </div>
      )}
    </div>
  )
}
