// Set de iconos trazados (20x20, un solo estilo) usado en toda la app.

type Props = { size?: number; className?: string }

const base = { fill: "none", stroke: "currentColor", strokeWidth: 1.6, strokeLinecap: "round" as const, strokeLinejoin: "round" as const }

export function IconoPanel({ size = 20, className }: Props) {
  return (
    <svg viewBox="0 0 20 20" width={size} height={size} className={className} {...base}>
      <rect x="2.5" y="2.5" width="6.5" height="6.5" rx="1.6" />
      <rect x="11" y="2.5" width="6.5" height="6.5" rx="1.6" />
      <rect x="2.5" y="11" width="6.5" height="6.5" rx="1.6" />
      <rect x="11" y="11" width="6.5" height="6.5" rx="1.6" />
    </svg>
  )
}

export function IconoInventario({ size = 20, className }: Props) {
  return (
    <svg viewBox="0 0 20 20" width={size} height={size} className={className} {...base}>
      <path d="M2.6 6.2 10 2.5l7.4 3.7v7.6L10 17.5 2.6 13.8Z" />
      <path d="M2.6 6.2 10 9.7l7.4-3.5" />
      <path d="M10 9.7V17.5" />
    </svg>
  )
}

export function IconoMovimientos({ size = 20, className }: Props) {
  return (
    <svg viewBox="0 0 20 20" width={size} height={size} className={className} {...base}>
      <path d="M3 7h11.3M14.3 7 10.9 3.6M14.3 7l-3.4 3.4" />
      <path d="M17 13H5.7M5.7 13l3.4-3.4M5.7 13l3.4 3.4" />
    </svg>
  )
}

export function IconoReportes({ size = 20, className }: Props) {
  return (
    <svg viewBox="0 0 20 20" width={size} height={size} className={className} {...base}>
      <path d="M3 17V11M9.2 17V7M15.4 17V3" />
      <path d="M2.5 17h15" />
    </svg>
  )
}

export function IconoAlertas({ size = 20, className }: Props) {
  return (
    <svg viewBox="0 0 20 20" width={size} height={size} className={className} {...base}>
      <path d="M6 8.2a4 4 0 0 1 8 0c0 3.1 1 4.2 1.5 4.9H4.5C5 12.4 6 11.3 6 8.2Z" />
      <path d="M8.3 15.6a1.8 1.8 0 0 0 3.4 0" />
    </svg>
  )
}

export function IconoImportar({ size = 20, className }: Props) {
  return (
    <svg viewBox="0 0 20 20" width={size} height={size} className={className} {...base}>
      <path d="M10 3v9M10 3l3.1 3.1M10 3 6.9 6.1" />
      <path d="M3.6 13.4v2.2c0 .72.6 1.3 1.3 1.3h10.2c.72 0 1.3-.58 1.3-1.3v-2.2" />
    </svg>
  )
}

export function IconoBuscar({ size = 20, className }: Props) {
  return (
    <svg viewBox="0 0 20 20" width={size} height={size} className={className} {...base}>
      <circle cx="8.6" cy="8.6" r="5" />
      <path d="M16.4 16.4 12.7 12.7" />
    </svg>
  )
}

export function IconoChevronAbajo({ size = 20, className }: Props) {
  return (
    <svg viewBox="0 0 20 20" width={size} height={size} className={className} {...base}>
      <path d="M5 7.5 10 12.5 15 7.5" />
    </svg>
  )
}

export function IconoFlecha({ size = 20, className }: Props) {
  return (
    <svg viewBox="0 0 20 20" width={size} height={size} className={className} {...base}>
      <path d="M4 10h11.3M10.8 5.5 15.3 10l-4.5 4.5" />
    </svg>
  )
}

export function IconoCandado({ size = 20, className }: Props) {
  return (
    <svg viewBox="0 0 20 20" width={size} height={size} className={className} {...base}>
      <rect x="4.5" y="9" width="11" height="8" rx="1.8" />
      <path d="M6.8 9V6.5a3.2 3.2 0 0 1 6.4 0V9" />
    </svg>
  )
}

export function IconoCandadoAbierto({ size = 20, className }: Props) {
  return (
    <svg viewBox="0 0 20 20" width={size} height={size} className={className} {...base}>
      <rect x="4.5" y="9" width="11" height="8" rx="1.8" />
      <path d="M6.8 9V6.5a3.2 3.2 0 0 1 6.2-1" />
    </svg>
  )
}

export function IconoCheck({ size = 20, className }: Props) {
  return (
    <svg viewBox="0 0 20 20" width={size} height={size} className={className} {...base}>
      <circle cx="10" cy="10" r="7.4" />
      <path d="M6.8 10.2 8.8 12.2 13.2 7.6" />
    </svg>
  )
}

export function IconoAlerta({ size = 20, className }: Props) {
  return (
    <svg viewBox="0 0 20 20" width={size} height={size} className={className} {...base} strokeLinejoin="round">
      <path d="M10 3.3 17.2 15.7H2.8Z" />
      <path d="M10 8v3.4" />
      <circle cx="10" cy="14.1" r="0.9" fill="currentColor" stroke="none" />
    </svg>
  )
}

export function IconoAnalitica({ size = 20, className }: Props) {
  return (
    <svg viewBox="0 0 20 20" width={size} height={size} className={className} {...base}>
      <path d="M2.5 17h15" />
      <path d="M3.5 13.2 7.8 9l2.9 2.6 5.8-6.3" />
      <path d="M13.2 5.3h3.3v3.3" />
    </svg>
  )
}

export function IconoDescargar({ size = 20, className }: Props) {
  return (
    <svg viewBox="0 0 20 20" width={size} height={size} className={className} {...base}>
      <path d="M10 3v9M10 12l3.1-3.1M10 12 6.9 8.9" />
      <path d="M3.6 13.4v2.2c0 .72.6 1.3 1.3 1.3h10.2c.72 0 1.3-.58 1.3-1.3v-2.2" />
    </svg>
  )
}

export function IconoArchivo({ size = 20, className }: Props) {
  return (
    <svg viewBox="0 0 20 20" width={size} height={size} className={className} {...base}>
      <path d="M6 2.6h6l3.4 3.4v11.4H6Z" />
      <path d="M12 2.6v3.4h3.4" />
    </svg>
  )
}

export function IconoNube({ size = 40, className }: Props) {
  return (
    <svg viewBox="0 0 40 40" width={size} height={size} className={className} {...base} strokeWidth={2}>
      <path d="M12 27h16a6 6 0 0 0 1-11.9A9 9 0 0 0 12 13.5 6.5 6.5 0 0 0 12 27Z" />
      <path d="M20 30V19M20 19l-4 4M20 19l4 4" />
    </svg>
  )
}
