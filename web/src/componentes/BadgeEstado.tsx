export function BadgeEstado({ estado }: { estado: 'normal' | 'bajo' | 'critico' | 'agotado' }) {
  const estilos = {
    normal: 'border-emerald-100 bg-emerald-50 text-emerald-700',
    bajo: 'border-orange-100 bg-orange-50 text-orange-700',
    critico: 'border-red-100 bg-red-50 text-red-700',
    agotado: 'border-red-200 bg-red-100 text-red-800',
  }[estado]
  const etiqueta = { normal: 'Normal', bajo: 'Stock bajo', critico: 'Crítico', agotado: 'Agotado' }[estado]
  const punto = { normal: 'bg-emerald-600', bajo: 'bg-orange-500', critico: 'bg-red-500', agotado: 'bg-red-700' }[estado]

  return (
    <span className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-full border px-2.5 py-1 text-[11px] font-extrabold ${estilos}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${punto}`} />
      {etiqueta}
    </span>
  )
}
