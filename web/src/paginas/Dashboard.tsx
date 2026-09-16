import type { ReactElement } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { Link } from 'react-router-dom'
import { Estado } from '../componentes/Estado'
import { Cabecera } from '../componentes/Cabecera'
import { BotonPrimario } from '../componentes/Boton'
import { IconoAlertas, IconoArchivo, IconoBuscar, IconoCheck, IconoImportar, IconoInventario, IconoMovimientos, IconoReportes, IconoFlecha } from '../componentes/Icono'
import { formatearLempiras } from '../lib/api'
import { hexCategoria } from '../lib/colores'
import { useAlertas, useImportaciones, useMovimientos, useProductos, useStockPorCategoria } from '../lib/consultas'

export function Dashboard() {
  const stock = useStockPorCategoria()
  const alertas = useAlertas(null)
  const productos = useProductos()
  const movimientos = useMovimientos({})
  const importaciones = useImportaciones()

  const totalProductos = productos.data?.length ?? 0
  const numCategorias = stock.data?.length ?? 0
  const valorTotal = stock.data?.reduce((s, c) => s + c.valor_total, 0) ?? 0
  const totalMovimientos = movimientos.data?.length ?? 0
  const entradas = movimientos.data?.filter((m) => m.tipo === 'E').reduce((s, m) => s + m.cantidad, 0) ?? 0
  const salidas = movimientos.data?.filter((m) => m.tipo === 'S').reduce((s, m) => s + m.cantidad, 0) ?? 0

  return (
    <div className="flex flex-col">
      <Cabecera titulo="Panel" subtitulo="Resumen del inventario en tiempo real.">
        <div className="flex items-center gap-2 rounded-[9px] border border-neutral-200 bg-neutral-50 px-3 py-2 text-neutral-400">
          <IconoBuscar size={16} />
          <span className="text-[13px] font-semibold">Buscar producto...</span>
        </div>
        <Link to="/importar">
          <BotonPrimario>
            <IconoImportar size={16} />
            Importar CSV
          </BotonPrimario>
        </Link>
      </Cabecera>

      <div className="flex flex-col gap-6 px-8 py-7">
        <div className="flex gap-4">
          <Tarjeta etiqueta="Productos" valor={totalProductos.toString()} caption={`en ${numCategorias} categorías`} Icono={IconoInventario} />
          <Tarjeta etiqueta="Valor de inventario" valor={formatearLempiras(valorTotal)} caption="al precio unitario actual" Icono={IconoReportes} />
          <Tarjeta etiqueta="Movimientos" valor={totalMovimientos.toString()} caption={`${entradas.toLocaleString('es-HN')} entradas · ${salidas.toLocaleString('es-HN')} salidas`} Icono={IconoMovimientos} />
          <Tarjeta
            etiqueta="Alertas de stock bajo"
            valor={(alertas.data?.length ?? 0).toString()}
            caption="requieren reposición"
            Icono={IconoAlertas}
            resaltar={(alertas.data?.length ?? 0) > 0}
          />
        </div>

        <div className="flex items-stretch gap-5">
          <div className="flex-[2] rounded-[14px] border border-neutral-200 bg-white p-6">
            <h2 className="text-sm font-extrabold text-neutral-900">Stock total por categoría</h2>
            <p className="text-xs font-semibold text-neutral-500">Unidades en inventario, agrupadas por categoría</p>
            <Estado cargando={stock.isLoading} error={stock.error} vacio={stock.data?.length === 0}>
              <div className="mt-4 h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={stock.data} margin={{ top: 16, left: 0, right: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e5e5" />
                    <XAxis dataKey="nombre" fontSize={11} fontWeight={600} stroke="#a3a3a3" tickLine={false} />
                    <YAxis fontSize={11} stroke="#a3a3a3" tickLine={false} axisLine={false} />
                    <Tooltip formatter={(valor) => Number(valor ?? 0).toLocaleString('es-HN')} />
                    <Bar dataKey="stock_total" radius={[4, 4, 2, 2]}>
                      {stock.data?.map((c) => (
                        <Cell key={c.id_categoria} fill={hexCategoria(c.id_categoria)} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Estado>
          </div>

          <div className="flex-1 rounded-[14px] border border-neutral-200 bg-white p-6">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-extrabold text-neutral-900">Alertas de stock bajo</h2>
              <Link to="/alertas" className="flex items-center gap-1 text-xs font-bold text-neutral-600 hover:text-neutral-900">
                Ver todas <IconoFlecha size={13} />
              </Link>
            </div>
            <Estado cargando={alertas.isLoading} error={alertas.error} vacio={alertas.data?.length === 0} mensajeVacio="Sin alertas activas.">
              <div className="mt-1">
                {alertas.data?.slice(0, 4).map((a) => (
                  <div key={a.codigo} className="flex items-center gap-3 border-b border-neutral-100 py-2.5 last:border-0">
                    <span className="h-1.5 w-1.5 flex-shrink-0 rounded-full bg-red-600" />
                    <div className="min-w-0 flex-1">
                      <div className="truncate text-[13px] font-bold text-neutral-900">{a.nombre}</div>
                      <div className="text-[11.5px] font-semibold text-neutral-500">
                        {a.codigo} · {a.stock_actual}/{a.minimo} uds
                      </div>
                    </div>
                    <span className="text-xs font-extrabold text-red-600">{a.diferencia}</span>
                  </div>
                ))}
              </div>
            </Estado>
          </div>
        </div>

        <div className="rounded-[14px] border border-neutral-200 bg-white p-6">
          <h2 className="text-sm font-extrabold text-neutral-900">Actividad reciente</h2>
          <p className="mb-1 text-xs font-semibold text-neutral-500">Últimas importaciones de CSV</p>
          <Estado
            cargando={importaciones.isLoading}
            error={importaciones.error}
            vacio={importaciones.data?.length === 0}
            mensajeVacio="Todavía no se ha importado ningún archivo."
          >
            <div>
              {importaciones.data?.map((nombre) => (
                <div key={nombre} className="flex items-center gap-3 border-b border-neutral-100 py-3 last:border-0">
                  <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-neutral-100 text-neutral-600">
                    <IconoArchivo size={15} />
                  </div>
                  <span className="flex-1 font-mono text-[13px] font-bold text-neutral-900">{nombre}</span>
                  <span className="flex items-center gap-1.5 text-xs font-bold text-emerald-700">
                    <IconoCheck size={14} /> importado
                  </span>
                </div>
              ))}
            </div>
          </Estado>
        </div>
      </div>
    </div>
  )
}

function Tarjeta({
  etiqueta,
  valor,
  caption,
  Icono,
  resaltar = false,
}: {
  etiqueta: string
  valor: string
  caption: string
  Icono: (p: { size?: number; className?: string }) => ReactElement
  resaltar?: boolean
}) {
  return (
    <div className="flex flex-1 flex-col gap-3 rounded-[14px] border border-neutral-200 bg-white p-5">
      <div className="flex items-center justify-between">
        <span className="text-[11.5px] font-extrabold uppercase tracking-wide text-neutral-500">{etiqueta}</span>
        <div
          className={`flex h-[30px] w-[30px] items-center justify-center rounded-lg ${
            resaltar ? 'bg-red-50 text-red-600' : 'bg-neutral-100 text-neutral-700'
          }`}
        >
          <Icono size={16} />
        </div>
      </div>
      <span className={`text-[26px] font-extrabold tracking-tight ${resaltar ? 'text-red-600' : 'text-neutral-900'}`}>{valor}</span>
      <span className="text-xs font-semibold text-neutral-500">{caption}</span>
    </div>
  )
}
