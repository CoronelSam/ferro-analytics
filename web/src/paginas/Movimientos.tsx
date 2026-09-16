import { useState, type ReactNode } from 'react'
import { Estado } from '../componentes/Estado'
import { Cabecera } from '../componentes/Cabecera'
import { BotonFantasma, BotonPrimario } from '../componentes/Boton'
import { IconoDescargar, IconoImportar } from '../componentes/Icono'
import { useMovimientos } from '../lib/consultas'

const OPCIONES_TIPO = [
  { valor: '', etiqueta: 'Todos' },
  { valor: 'E', etiqueta: 'Entradas' },
  { valor: 'S', etiqueta: 'Salidas' },
] as const

export function Movimientos() {
  const [fechaDesde, setFechaDesde] = useState('')
  const [fechaHasta, setFechaHasta] = useState('')
  const [tipo, setTipo] = useState<'' | 'E' | 'S'>('')

  const movimientos = useMovimientos({
    fechaDesde: fechaDesde || undefined,
    fechaHasta: fechaHasta || undefined,
    tipo: tipo || undefined,
  })

  const entradas = movimientos.data?.filter((m) => m.tipo === 'E').reduce((s, m) => s + m.cantidad, 0) ?? 0
  const salidas = movimientos.data?.filter((m) => m.tipo === 'S').reduce((s, m) => s + m.cantidad, 0) ?? 0

  return (
    <div className="flex flex-col">
      <Cabecera titulo="Movimientos" subtitulo="Consulta entradas y salidas por período.">
        <BotonFantasma>
          <IconoDescargar size={16} />
          Exportar
        </BotonFantasma>
        <BotonPrimario>
          <IconoImportar size={16} />
          Importar movimientos
        </BotonPrimario>
      </Cabecera>

      <div className="flex flex-col gap-5 px-8 py-7">
        <div className="flex flex-wrap items-end justify-between gap-4 rounded-[14px] border border-neutral-200 bg-white px-6 py-5">
          <div className="flex items-end gap-4">
            <Campo etiqueta="Desde">
              <input
                type="date"
                value={fechaDesde}
                onChange={(e) => setFechaDesde(e.target.value)}
                className="w-[150px] rounded-[9px] border border-neutral-200 px-3 py-2 text-[13px] font-bold text-neutral-800"
              />
            </Campo>
            <Campo etiqueta="Hasta">
              <input
                type="date"
                value={fechaHasta}
                onChange={(e) => setFechaHasta(e.target.value)}
                className="w-[150px] rounded-[9px] border border-neutral-200 px-3 py-2 text-[13px] font-bold text-neutral-800"
              />
            </Campo>
            <Campo etiqueta="Tipo">
              <div className="flex gap-0.5 rounded-[9px] bg-neutral-100 p-[3px]">
                {OPCIONES_TIPO.map((o) => (
                  <button
                    key={o.valor}
                    onClick={() => setTipo(o.valor)}
                    className={`rounded-[7px] px-3.5 py-2 text-[12.5px] font-bold ${
                      tipo === o.valor ? 'bg-white text-neutral-900 shadow-sm' : 'text-neutral-500'
                    }`}
                  >
                    {o.etiqueta}
                  </button>
                ))}
              </div>
            </Campo>
          </div>

          {movimientos.data && (
            <div className="flex gap-2.5">
              <Chip etiqueta="movimientos" valor={movimientos.data.length.toLocaleString('es-HN')} />
              <Chip etiqueta="entradas" valor={entradas.toLocaleString('es-HN')} color="text-emerald-700" />
              <Chip etiqueta="salidas" valor={salidas.toLocaleString('es-HN')} color="text-amber-700" />
            </div>
          )}
        </div>

        <Estado
          cargando={movimientos.isLoading}
          error={movimientos.error}
          vacio={movimientos.data?.length === 0}
          mensajeVacio="Sin movimientos para el filtro seleccionado."
        >
          <div className="overflow-hidden rounded-[14px] border border-neutral-200 bg-white">
            <table className="w-full text-sm">
              <thead className="bg-neutral-50 text-left text-[10.5px] font-extrabold uppercase tracking-wide text-neutral-500">
                <tr>
                  <th className="px-4 py-2.5">ID</th>
                  <th className="px-4 py-2.5">Producto</th>
                  <th className="px-4 py-2.5">Tipo</th>
                  <th className="px-4 py-2.5 text-right">Cantidad</th>
                  <th className="px-4 py-2.5">Fecha</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-100">
                {movimientos.data?.map((m) => (
                  <tr key={m.id_movimiento}>
                    <td className="px-4 py-3 text-[12.5px] font-semibold text-neutral-500">{m.id_movimiento}</td>
                    <td className="px-4 py-3 font-mono text-xs font-bold text-neutral-800">{m.codigo_producto}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`rounded-full px-2.5 py-1 text-xs font-extrabold ${
                          m.tipo === 'E' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'
                        }`}
                      >
                        {m.tipo === 'E' ? 'Entrada' : 'Salida'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right text-[13px] font-bold text-neutral-900">{m.cantidad}</td>
                    <td className="px-4 py-3 text-[12.5px] font-semibold text-neutral-500">{m.fecha}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Estado>
      </div>
    </div>
  )
}

function Campo({ etiqueta, children }: { etiqueta: string; children: ReactNode }) {
  return (
    <div className="flex flex-col gap-1.5">
      <span className="text-[11px] font-extrabold uppercase tracking-wide text-neutral-500">{etiqueta}</span>
      {children}
    </div>
  )
}

function Chip({ etiqueta, valor, color = 'text-neutral-800' }: { etiqueta: string; valor: string; color?: string }) {
  return (
    <div className="flex items-baseline gap-1.5 rounded-[9px] border border-neutral-200 bg-neutral-50 px-3.5 py-2">
      <span className={`text-sm font-extrabold ${color}`}>{valor}</span>
      <span className="text-[11.5px] font-bold text-neutral-500">{etiqueta}</span>
    </div>
  )
}
