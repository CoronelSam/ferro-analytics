import { useMemo, useState, type ReactNode } from 'react'
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { Estado } from '../componentes/Estado'
import { Cabecera } from '../componentes/Cabecera'
import { BotonFantasma } from '../componentes/Boton'
import { IconoChevronAbajo, IconoDescargar } from '../componentes/Icono'
import { formatearLempiras } from '../lib/api'
import { hexCategoria } from '../lib/colores'
import { descargarCSV } from '../lib/csv'
import { useCategorias, useTopInmovilizado, useVentasMensuales } from '../lib/consultas'
import type { Categoria, ProductoInmovilizado, VentaMensualCategoria } from '../lib/tipos'

type Pestana = 'inmovilizado' | 'ventas'

const OPCIONES_DIAS = [30, 60, 90, 180] as const
const OPCIONES_N = [10, 20, 50] as const

const NOMBRES_MES = [
  'ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic',
]

function formatearMes(clave: string): string {
  const [anio, mes] = clave.split('-')
  return `${NOMBRES_MES[Number(mes) - 1]} ${anio}`
}

export function Reportes() {
  const [pestana, setPestana] = useState<Pestana>('inmovilizado')
  const categorias = useCategorias()

  const [dias, setDias] = useState<number>(90)
  const [n, setN] = useState<number>(10)
  const [categoriaInmovilizado, setCategoriaInmovilizado] = useState<number | null>(null)
  const inmovilizado = useTopInmovilizado(n, dias)
  const filasInmovilizado = useMemo(
    () =>
      (inmovilizado.data ?? []).filter(
        (p) => categoriaInmovilizado === null || p.id_categoria === categoriaInmovilizado,
      ),
    [inmovilizado.data, categoriaInmovilizado],
  )

  const [categoriaVentas, setCategoriaVentas] = useState<number | null>(null)
  const ventas = useVentasMensuales()
  const filasVentas = useMemo(
    () => (ventas.data ?? []).filter((v) => categoriaVentas === null || v.id_categoria === categoriaVentas),
    [ventas.data, categoriaVentas],
  )

  const hayDatosExportar = pestana === 'inmovilizado' ? !!filasInmovilizado.length : !!filasVentas.length

  return (
    <div className="flex flex-col">
      <Cabecera titulo="Reportes" subtitulo="Top inmovilizado y ventas mensuales por categoría.">
        <BotonFantasma
          onClick={() =>
            pestana === 'inmovilizado'
              ? descargarCSV('top_inmovilizado', filasInmovilizado)
              : descargarCSV('ventas_mensuales', filasVentas)
          }
          disabled={!hayDatosExportar}
        >
          <IconoDescargar size={16} />
          Exportar CSV
        </BotonFantasma>
      </Cabecera>

      <div className="flex flex-col gap-5 px-8 py-7">
        <div className="flex border-b border-[#DCE5EF]">
          <PestanaBoton activa={pestana === 'inmovilizado'} onClick={() => setPestana('inmovilizado')}>
            Top inmovilizado
          </PestanaBoton>
          <PestanaBoton activa={pestana === 'ventas'} onClick={() => setPestana('ventas')}>
            Ventas mensuales por categoría
          </PestanaBoton>
        </div>
        {pestana === 'inmovilizado' ? (
          <TopInmovilizado
            reporte={inmovilizado}
            filas={filasInmovilizado}
            categorias={categorias.data ?? []}
            dias={dias}
            setDias={setDias}
            n={n}
            setN={setN}
            idCategoria={categoriaInmovilizado}
            setIdCategoria={setCategoriaInmovilizado}
          />
        ) : (
          <VentasMensuales
            reporte={ventas}
            filas={filasVentas}
            categorias={categorias.data ?? []}
            idCategoria={categoriaVentas}
            setIdCategoria={setCategoriaVentas}
          />
        )}
      </div>
    </div>
  )
}

function PestanaBoton({ activa, onClick, children }: { activa: boolean; onClick: () => void; children: string }) {
  return (
    <button
      onClick={onClick}
      className={`-mb-px border-b-2 px-1 py-2.5 mr-6 text-[13.5px] font-extrabold ${
        activa ? 'border-[#124E96] text-[#124E96]' : 'border-transparent text-[#6D7B8F]'
      }`}
    >
      {children}
    </button>
  )
}

function SelectorCategoria({
  categorias,
  idCategoria,
  onChange,
}: {
  categorias: Categoria[]
  idCategoria: number | null
  onChange: (id: number | null) => void
}) {
  return (
    <div className="relative">
      <select
        value={idCategoria ?? ''}
        onChange={(e) => onChange(e.target.value ? Number(e.target.value) : null)}
        className="appearance-none rounded-xl border border-[#DCE5EF] bg-white py-2.5 pl-3.5 pr-9 text-[12.5px] font-bold text-[#43566F]"
      >
        <option value="">Todas las categorías</option>
        {categorias.map((c) => (
          <option key={c.id} value={c.id}>
            {c.nombre}
          </option>
        ))}
      </select>
      <IconoChevronAbajo size={13} className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-[#6D7B8F]" />
    </div>
  )
}

function Chip({ etiqueta, valor, color = 'text-[#243B55]' }: { etiqueta: string; valor: string; color?: string }) {
  return (
    <div className="flex items-baseline gap-1.5 rounded-[9px] border border-[#DCE5EF] bg-[#F5F8FC] px-3.5 py-2">
      <span className={`text-sm font-extrabold ${color}`}>{valor}</span>
      <span className="text-[11.5px] font-bold text-[#6D7B8F]">{etiqueta}</span>
    </div>
  )
}

function TopInmovilizado({
  reporte,
  filas,
  categorias,
  dias,
  setDias,
  n,
  setN,
  idCategoria,
  setIdCategoria,
}: {
  reporte: { isLoading: boolean; error: Error | null; data?: ProductoInmovilizado[] }
  filas: ProductoInmovilizado[]
  categorias: Categoria[]
  dias: number
  setDias: (v: number) => void
  n: number
  setN: (v: number) => void
  idCategoria: number | null
  setIdCategoria: (id: number | null) => void
}) {
  const valorTotal = filas.reduce((s, p) => s + p.valor_inmovilizado, 0)
  const stockTotal = filas.reduce((s, p) => s + p.stock_actual, 0)
  const sinSalidas = filas.filter((p) => p.ultima_salida === null).length

  return (
    <div className="flex flex-col gap-5">
      <div className="fa-toolbar flex flex-wrap items-center gap-2.5 p-3.5">
        <Campo etiqueta="Categoría">
          <SelectorCategoria categorias={categorias} idCategoria={idCategoria} onChange={setIdCategoria} />
        </Campo>
        <Campo etiqueta="Días sin salida">
          <div className="relative">
            <select
              value={dias}
              onChange={(e) => setDias(Number(e.target.value))}
              className="appearance-none rounded-xl border border-[#DCE5EF] bg-white py-2.5 pl-3.5 pr-9 text-[12.5px] font-bold text-[#43566F]"
            >
              {OPCIONES_DIAS.map((d) => (
                <option key={d} value={d}>
                  {d} días o más
                </option>
              ))}
            </select>
            <IconoChevronAbajo size={13} className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-[#6D7B8F]" />
          </div>
        </Campo>
        <Campo etiqueta="Cantidad">
          <div className="relative">
            <select
              value={n}
              onChange={(e) => setN(Number(e.target.value))}
              className="appearance-none rounded-xl border border-[#DCE5EF] bg-white py-2.5 pl-3.5 pr-9 text-[12.5px] font-bold text-[#43566F]"
            >
              {OPCIONES_N.map((v) => (
                <option key={v} value={v}>
                  Top {v}
                </option>
              ))}
            </select>
            <IconoChevronAbajo size={13} className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-[#6D7B8F]" />
          </div>
        </Campo>

        <div className="ml-auto flex gap-2.5">
          <Chip etiqueta="productos" valor={filas.length.toLocaleString('es-HN')} />
          <Chip etiqueta="valor inmovilizado" valor={formatearLempiras(valorTotal)} />
          <Chip etiqueta="sin salidas nunca" valor={sinSalidas.toLocaleString('es-HN')} color="text-amber-700" />
          <Chip etiqueta="unidades en stock" valor={stockTotal.toLocaleString('es-HN')} />
        </div>
      </div>

      <Estado
        cargando={reporte.isLoading}
        error={reporte.error}
        vacio={filas.length === 0}
        mensajeVacio={
          reporte.data?.length
            ? 'Ningún producto inmovilizado coincide con los filtros seleccionados.'
            : `No hay productos con ${dias} días o más sin salidas.`
        }
      >
        <div className="fa-table-wrap">
          <table className="w-full text-sm">
            <thead className="bg-[#F5F8FC] text-left text-[10.5px] font-extrabold uppercase tracking-wide text-[#6D7B8F]">
              <tr>
                <th className="px-4 py-2.5">Código</th>
                <th className="px-4 py-2.5">Nombre</th>
                <th className="px-4 py-2.5 text-right">Stock</th>
                <th className="px-4 py-2.5 text-right">Valor inmovilizado</th>
                <th className="px-4 py-2.5">Última salida</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-100">
              {filas.map((p) => (
                <tr key={p.codigo}>
                  <td className="px-4 py-3 font-mono text-xs font-bold text-[#3E536C]">{p.codigo}</td>
                  <td className="px-4 py-3 text-[13px] font-bold text-[#13233A]">{p.nombre}</td>
                  <td className="px-4 py-3 text-right text-[13px] font-semibold text-[#3E536C]">{p.stock_actual}</td>
                  <td className="px-4 py-3 text-right text-[13px] font-bold text-[#13233A]">{formatearLempiras(p.valor_inmovilizado)}</td>
                  <td className="px-4 py-3 text-[12.5px] font-semibold text-[#6D7B8F]">{p.ultima_salida ?? 'Sin salidas'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Estado>
    </div>
  )
}

function VentasMensuales({
  reporte,
  filas,
  categorias,
  idCategoria,
  setIdCategoria,
}: {
  reporte: { isLoading: boolean; error: Error | null; data?: VentaMensualCategoria[] }
  filas: VentaMensualCategoria[]
  categorias: Categoria[]
  idCategoria: number | null
  setIdCategoria: (id: number | null) => void
}) {
  const colorPorNombre = useMemo(() => {
    const m = new Map<string, string>()
    categorias.forEach((c) => m.set(c.nombre, hexCategoria(c.id)))
    return m
  }, [categorias])

  const { series, nombresCategoria } = useMemo(() => {
    const nombres = [...new Set(filas.map((d) => d.nombre_categoria))]
    const porMes = new Map<string, Record<string, number | string>>()

    for (const d of filas) {
      const clave = `${d.anio}-${String(d.mes).padStart(2, '0')}`
      const fila = porMes.get(clave) ?? { mes: clave }
      fila[d.nombre_categoria] = d.unidades
      porMes.set(clave, fila)
    }

    return {
      series: [...porMes.values()].sort((a, b) => (a.mes as string).localeCompare(b.mes as string)),
      nombresCategoria: nombres,
    }
  }, [filas])

  const totalesPorCategoria = useMemo(() => {
    const totales = new Map<string, number>()
    for (const d of filas) {
      totales.set(d.nombre_categoria, (totales.get(d.nombre_categoria) ?? 0) + d.unidades)
    }
    return [...totales.entries()]
      .map(([nombre, total]) => ({ nombre, total }))
      .sort((a, b) => b.total - a.total)
  }, [filas])

  const resumenCategoriaUnica = useMemo(() => {
    if (idCategoria === null || filas.length === 0) return null
    const total = filas.reduce((s, d) => s + d.unidades, 0)
    const pico = filas.reduce((max, d) => (d.unidades > max.unidades ? d : max), filas[0])
    return {
      total,
      promedio: total / filas.length,
      mesPico: `${formatearMes(`${pico.anio}-${String(pico.mes).padStart(2, '0')}`)} (${pico.unidades.toLocaleString('es-HN')})`,
    }
  }, [filas, idCategoria])

  return (
    <div className="flex flex-col gap-5">
      <div className="fa-toolbar flex flex-wrap items-center gap-2.5 p-3.5">
        <Campo etiqueta="Categoría">
          <SelectorCategoria categorias={categorias} idCategoria={idCategoria} onChange={setIdCategoria} />
        </Campo>

        {resumenCategoriaUnica && (
          <div className="ml-auto flex gap-2.5">
            <Chip etiqueta="unidades del período" valor={resumenCategoriaUnica.total.toLocaleString('es-HN')} />
            <Chip etiqueta="promedio mensual" valor={resumenCategoriaUnica.promedio.toLocaleString('es-HN', { maximumFractionDigits: 1 })} />
            <Chip etiqueta="mes pico" valor={resumenCategoriaUnica.mesPico} />
          </div>
        )}
      </div>

      <Estado
        cargando={reporte.isLoading}
        error={reporte.error}
        vacio={series.length === 0}
        mensajeVacio={
          reporte.data?.length ? 'Esta categoría no tiene ventas registradas.' : 'No hay ventas registradas todavía.'
        }
      >
        <div className="flex flex-col gap-5">
          <div className="h-96 fa-card p-6">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={series}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e5e5" />
                <XAxis dataKey="mes" tickFormatter={formatearMes} fontSize={11} fontWeight={600} stroke="#a3a3a3" tickLine={false} />
                <YAxis fontSize={11} stroke="#a3a3a3" tickLine={false} axisLine={false} />
                <Tooltip labelFormatter={(v) => formatearMes(String(v))} />
                <Legend wrapperStyle={{ fontSize: 12.5, fontWeight: 700 }} />
                {nombresCategoria.map((nombre) => (
                  <Line
                    key={nombre}
                    type="monotone"
                    dataKey={nombre}
                    stroke={colorPorNombre.get(nombre) ?? '#171717'}
                    strokeWidth={idCategoria === null ? 2.25 : 3}
                    dot={idCategoria !== null}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>

          {idCategoria === null && (
            <div className="fa-table-wrap">
              <table className="w-full text-sm">
                <thead className="bg-[#F5F8FC] text-left text-[10.5px] font-extrabold uppercase tracking-wide text-[#6D7B8F]">
                  <tr>
                    <th className="px-4 py-2.5">Categoría</th>
                    <th className="px-4 py-2.5 text-right">Unidades vendidas en el período</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-100">
                  {totalesPorCategoria.map((c) => (
                    <tr key={c.nombre}>
                      <td className="px-4 py-3 text-[13px] font-bold text-[#13233A]">{c.nombre}</td>
                      <td className="px-4 py-3 text-right text-[13px] font-semibold text-[#3E536C]">{c.total.toLocaleString('es-HN')}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </Estado>
    </div>
  )
}

function Campo({ etiqueta, children }: { etiqueta: string; children: ReactNode }) {
  return (
    <div className="flex flex-col gap-1.5">
      <span className="text-[11px] font-extrabold uppercase tracking-wide text-[#6D7B8F]">{etiqueta}</span>
      {children}
    </div>
  )
}
