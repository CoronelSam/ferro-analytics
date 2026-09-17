import type { ReactNode } from 'react'

export function TarjetaSeccion({
  titulo,
  subtitulo,
  accion,
  children,
  className = '',
}: {
  titulo?: string
  subtitulo?: string
  accion?: ReactNode
  children: ReactNode
  className?: string
}) {
  return (
    <section className={`fa-card p-6 ${className}`}>
      {(titulo || subtitulo || accion) && (
        <div className="mb-4 flex items-start justify-between gap-4">
          <div>
            {titulo && <h2 className="text-sm font-extrabold text-[#13233A]">{titulo}</h2>}
            {subtitulo && <p className="mt-0.5 text-xs font-semibold text-[#6D7B8F]">{subtitulo}</p>}
          </div>
          {accion}
        </div>
      )}
      {children}
    </section>
  )
}
