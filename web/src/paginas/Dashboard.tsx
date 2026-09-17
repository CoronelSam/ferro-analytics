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
import { TarjetaMetrica } from '../componentes/TarjetaMetrica'
import { TarjetaSeccion } from '../componentes/TarjetaSeccion'
import {
  IconoAlertas,
  IconoArchivo,
  IconoBuscar,
  IconoCheck,
  IconoImportar,
  IconoInventario,
  IconoMovimientos,
  IconoReportes,
  IconoFlecha,
} from '../componentes/Icono'
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
  const alertasActivas = alertas.data?.length ?? 0
  const categoriaMayorStock = [...(stock.data ?? [])].sort((a, b) => b.stock_total - a.stock_total)[0]

  return (
    <div className="flex flex-col">
      <Cabecera titulo="Panel" subtitulo="Resumen visual del inventario y su actividad reciente.">
        <div className="flex items-center gap-2 rounded-xl border border-[#DCE5EF] bg-[#F8FAFD] px-3 py-2 text-[#7B8DA3]">
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
        <div className="grid grid-cols-4 gap-4">
          <TarjetaMetrica etiqueta="Productos" valor={totalProductos.toLocaleString('es-HN')} caption={`en ${numCategorias} categorías`} Icono={IconoInventario} />
          <TarjetaMetrica etiqueta="Valor de inventario" valor={formatearLempiras(valorTotal)} caption="al precio unitario actual" Icono={IconoReportes} tono="naranja" />
          <TarjetaMetrica etiqueta="Movimientos" valor={totalMovimientos.toLocaleString('es-HN')} caption={`${entradas.toLocaleString('es-HN')} entradas · ${salidas.toLocaleString('es-HN')} salidas`} Icono={IconoMovimientos} />
          <TarjetaMetrica etiqueta="Stock bajo" valor={alertasActivas.toString()} caption="productos requieren reposición" Icono={IconoAlertas} tono={alertasActivas > 0 ? 'alerta' : 'azul'} />
        </div>

        <div className="fa-toolbar grid grid-cols-3 divide-x divide-[#E5ECF4] px-2 py-3">
          <Insight etiqueta="Estado del inventario" valor={alertasActivas === 0 ? 'Sin alertas activas' : `${alertasActivas} productos por revisar`} />
          <Insight etiqueta="Categoría con más stock" valor={categoriaMayorStock?.nombre ?? 'Sin datos'} />
          <Insight etiqueta="Flujo registrado" valor={`${entradas.toLocaleString('es-HN')} entradas / ${salidas.toLocaleString('es-HN')} salidas`} />
        </div>

        <div className="grid grid-cols-[minmax(0,2fr)_minmax(310px,1fr)] gap-5">
          <TarjetaSeccion titulo="Stock total por categoría" subtitulo="Unidades disponibles agrupadas por categoría.">
            <Estado cargando={stock.isLoading} error={stock.error} vacio={stock.data?.length === 0}>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={stock.data} margin={{ top: 16, left: 0, right: 8, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="4 4" vertical={false} stroke="#E8EEF5" />
                    <XAxis dataKey="nombre" fontSize={11} fontWeight={700} stroke="#7C8DA2" tickLine={false} axisLine={false} />
                    <YAxis fontSize={11} fontWeight={600} stroke="#91A0B2" tickLine={false} axisLine={false} />
                    <Tooltip formatter={(valor) => Number(valor ?? 0).toLocaleString('es-HN')} cursor={{ fill: '#F7F9FC' }} />
                    <Bar dataKey="stock_total" radius={[7, 7, 2, 2]} maxBarSize={46}>
                      {stock.data?.map((c) => <Cell key={c.id_categoria} fill={hexCategoria(c.id_categoria)} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Estado>
          </TarjetaSeccion>

          <TarjetaSeccion
            titulo="Alertas de stock bajo"
            subtitulo="Productos que necesitan atención."
            accion={
              <Link to="/alertas" className="flex items-center gap-1 text-xs font-extrabold text-[#124E96] hover:text-[#0B2E59]">
                Ver todas <IconoFlecha size={13} />
              </Link>
            }
          >
            <Estado cargando={alertas.isLoading} error={alertas.error} vacio={alertas.data?.length === 0} mensajeVacio="Sin alertas activas.">
              <div className="-mb-2">
                {alertas.data?.slice(0, 5).map((a) => (
                  <div key={a.codigo} className="group flex items-center gap-3 border-b border-[#EDF2F7] py-3 last:border-0">
                    <span className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-[#FFF1E7] text-[#E65F00]">
                      <IconoAlertas size={15} />
                    </span>
                    <div className="min-w-0 flex-1">
                      <div className="truncate text-[12.5px] font-extrabold text-[#13233A]">{a.nombre}</div>
                      <div className="mt-0.5 text-[11px] font-semibold text-[#6D7B8F]">{a.codigo} · {a.stock_actual}/{a.minimo} uds</div>
                    </div>
                    <span className="rounded-full bg-[#FFF1E7] px-2 py-1 text-[10.5px] font-extrabold text-[#E65F00]">{a.diferencia} uds</span>
                  </div>
                ))}
              </div>
            </Estado>
          </TarjetaSeccion>
        </div>

        <TarjetaSeccion titulo="Actividad reciente" subtitulo="Últimas importaciones registradas en el sistema.">
          <Estado cargando={importaciones.isLoading} error={importaciones.error} vacio={importaciones.data?.length === 0} mensajeVacio="Todavía no se ha importado ningún archivo.">
            <div className="-mb-2">
              {importaciones.data?.map((nombre) => (
                <div key={nombre} className="flex items-center gap-3 border-b border-[#EDF2F7] py-3 last:border-0">
                  <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-xl bg-[#EAF2FC] text-[#124E96]">
                    <IconoArchivo size={16} />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="truncate font-mono text-[12.5px] font-extrabold text-[#13233A]">{nombre}</div>
                    <div className="mt-0.5 text-[11px] font-semibold text-[#6D7B8F]">Archivo procesado correctamente</div>
                  </div>
                  <span className="flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-1 text-[11px] font-extrabold text-emerald-700">
                    <IconoCheck size={13} /> Importado
                  </span>
                </div>
              ))}
            </div>
          </Estado>
        </TarjetaSeccion>
      </div>
    </div>
  )
}

function Insight({ etiqueta, valor }: { etiqueta: string; valor: string }) {
  return (
    <div className="px-4 py-1">
      <div className="text-[10px] font-extrabold uppercase tracking-[0.09em] text-[#8A98AA]">{etiqueta}</div>
      <div className="mt-1 truncate text-[12.5px] font-extrabold text-[#43566F]">{valor}</div>
    </div>
  )
}
