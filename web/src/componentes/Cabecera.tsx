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
    <header className="flex items-center justify-between border-b border-neutral-200 bg-white px-8 py-5">
      <div>
        <h1 className="text-[19px] font-extrabold tracking-tight text-neutral-900">{titulo}</h1>
        <p className="mt-0.5 text-[13px] font-medium text-neutral-500">{subtitulo}</p>
      </div>
      {children && <div className="flex items-center gap-2.5">{children}</div>}
    </header>
  )
}
