import type { ReactNode } from 'react'

export function Cabecera({
  titulo,
  subtitulo,
  children,
}: {
  titulo: string
  subtitulo: string
  children?: ReactNode
}) {
  return (
    <header className="sticky top-0 z-10 flex items-center justify-between border-b border-[#DCE5EF] bg-white px-8 py-5 shadow-[0_1px_0_rgba(11,46,89,0.015)]">
      <div className="flex items-start gap-3">
        <span className="mt-1 h-9 w-1.5 rounded-full bg-[#FF7A1A]" />
        <div>
          <h1 className="text-[20px] font-extrabold tracking-tight text-[#13233A]">{titulo}</h1>
          <p className="mt-0.5 text-[13px] font-semibold text-[#6D7B8F]">{subtitulo}</p>
        </div>
      </div>
      {children && <div className="flex items-center gap-2.5">{children}</div>}
    </header>
  )
}
