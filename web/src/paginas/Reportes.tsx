import { useMemo, useState } from 'react'
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
import { IconoDescargar } from '../componentes/Icono'
import { formatearLempiras } from '../lib/api'
import { hexCategoria } from '../lib/colores'
import { descargarCSV } from '../lib/csv'
import { useCategorias, useTopInmovilizado, useVentasMensuales } from '../lib/consultas'

type Pestana = 'inmovilizado' | 'ventas'

export function Reportes() {
  const [pestana, setPestana] = useState<Pestana>('inmovilizado')
  const inmovilizado = useTopInmovilizado(10, 90)
  const ventas = useVentasMensuales()

  const hayDatosExportar = pestana === 'inmovilizado' ? !!inmovilizado.data?.length : !!ventas.data?.length

  return (
    <div className="flex flex-col">
      <Cabecera titulo="Reportes" subtitulo="Top inmovilizado y ventas mensuales por categoría.">
        <BotonFantasma
          onClick={() =>
            pestana === 'inmovilizado'
              ? descargarCSV('top_inmovilizado', inmovilizado.data ?? [])
              : descargarCSV('ventas_mensuales', ventas.data ?? [])
          }
          disabled={!hayDatosExportar}
        >
          <IconoDescargar size={16} />
          Exportar CSV
        </BotonFantasma>
      </Cabecera>

      <div className="flex flex-col gap-5 px-8 py-7">
        <div className="flex border-b border-[#DCE5EF]">
          <Pestana activa={pestana === 'inmovilizado'} onClick={() => setPestana('inmovilizado')}>
            Top inmovilizado
          </Pestana>
          <Pestana activa={pestana === 'ventas'} onClick={() => setPestana('ventas')}>
            Ventas mensuales por categoría
          </Pestana>
        </div>
        {pestana === 'inmovilizado' ? <TopInmovilizado /> : <VentasMensuales />}
      </div>
    </div>
  )
}

function Pestana({ activa, onClick, children }: { activa: boolean; onClick: () => void; children: string }) {
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

function TopInmovilizado() {
  const reporte = useTopInmovilizado(10, 90)

  return (
    <Estado
      cargando={reporte.isLoading}
      error={reporte.error}
      vacio={reporte.data?.length === 0}
      mensajeVacio="No hay productos inmovilizados en los últimos 90 días."
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
            {reporte.data?.map((p) => (
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
  )
}

function VentasMensuales() {
  const reporte = useVentasMensuales()
  const categorias = useCategorias()

  const colorPorNombre = useMemo(() => {
    const m = new Map<string, string>()
    categorias.data?.forEach((c) => m.set(c.nombre, hexCategoria(c.id)))
    return m
  }, [categorias.data])

  const { filas, nombresCategoria } = useMemo(() => {
    const datos = reporte.data ?? []
    const nombres = [...new Set(datos.map((d) => d.nombre_categoria))]
    const porMes = new Map<string, Record<string, number | string>>()

    for (const d of datos) {
      const clave = `${d.anio}-${String(d.mes).padStart(2, '0')}`
      const fila = porMes.get(clave) ?? { mes: clave }
      fila[d.nombre_categoria] = d.unidades
      porMes.set(clave, fila)
    }

    return {
      filas: [...porMes.values()].sort((a, b) => (a.mes as string).localeCompare(b.mes as string)),
      nombresCategoria: nombres,
    }
  }, [reporte.data])

  return (
    <Estado
      cargando={reporte.isLoading}
      error={reporte.error}
      vacio={filas.length === 0}
      mensajeVacio="No hay ventas registradas todavía."
    >
      <div className="h-96 fa-card p-6">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={filas}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e5e5" />
            <XAxis dataKey="mes" fontSize={11} fontWeight={600} stroke="#a3a3a3" tickLine={false} />
            <YAxis fontSize={11} stroke="#a3a3a3" tickLine={false} axisLine={false} />
            <Tooltip />
            <Legend wrapperStyle={{ fontSize: 12.5, fontWeight: 700 }} />
            {nombresCategoria.map((nombre) => (
              <Line
                key={nombre}
                type="monotone"
                dataKey={nombre}
                stroke={colorPorNombre.get(nombre) ?? '#171717'}
                strokeWidth={2.25}
                dot={false}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Estado>
  )
}
