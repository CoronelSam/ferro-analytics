import { useMemo, useState, type ReactNode } from 'react'
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
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
import { descargarCSV } from '../lib/csv'
import {
  useCategorias,
  useClasificacionABCXYZ,
  useMigracionesABCXYZ,
  useProductosPrioritarios,
  usePronosticoCategoria,
  usePronosticoProducto,
  useResumenABCXYZ,
} from '../lib/consultas'
import type { ClaseABC, ClaseXYZ, ComparacionModelo } from '../lib/tipos'

type Pestana = 'clasificacion' | 'prediccion'

const CLASES_ABC: ClaseABC[] = ['A', 'B', 'C']
const CLASES_XYZ: ClaseXYZ[] = ['X', 'Y', 'Z']

const COLOR_ABC: Record<ClaseABC, string> = {
  A: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  B: 'bg-amber-50 text-amber-700 border-amber-200',
  C: 'bg-neutral-100 text-neutral-600 border-neutral-200',
}

// Etiquetas en lenguaje llano para las clases técnicas ABC/XYZ.
const ETIQUETA_ABC: Record<ClaseABC, string> = { A: 'Alta', B: 'Media', C: 'Baja' }
const ETIQUETA_XYZ: Record<ClaseXYZ, string> = { X: 'Estable', Y: 'Variable', Z: 'Irregular' }

const NOMBRES_MODELO: Record<string, string> = {
  ingenuo: 'Ingenuo',
  naive_estacional: 'Naive estacional',
  media_movil: 'Media móvil',
  suavizado_exponencial: 'Suavizado exponencial',
  regresion: 'Regresión (tendencia + estacionalidad)',
}

export function Analitica() {
  const [pestana, setPestana] = useState<Pestana>('clasificacion')
  const clasificacion = useClasificacionABCXYZ()

  return (
    <div className="flex flex-col">
      <Cabecera
        titulo="Analítica"
        subtitulo="Clasificación ABC-XYZ y predicción de demanda."
      >
        {pestana === 'clasificacion' && (
          <BotonFantasma
            onClick={() => descargarCSV('clasificacion_abc_xyz', clasificacion.data ?? [])}
            disabled={!clasificacion.data?.length}
          >
            <IconoDescargar size={16} />
            Exportar CSV
          </BotonFantasma>
        )}
      </Cabecera>

      <div className="flex flex-col gap-5 px-8 py-7">
        <div className="flex border-b border-neutral-200">
          <Pestana activa={pestana === 'clasificacion'} onClick={() => setPestana('clasificacion')}>
            Clasificación ABC-XYZ
          </Pestana>
          <Pestana activa={pestana === 'prediccion'} onClick={() => setPestana('prediccion')}>
            Predicción de demanda
          </Pestana>
        </div>
        {pestana === 'clasificacion' ? <ClasificacionABCXYZ /> : <PrediccionDemanda />}
      </div>
    </div>
  )
}

function Pestana({ activa, onClick, children }: { activa: boolean; onClick: () => void; children: string }) {
  return (
    <button
      onClick={onClick}
      className={`-mb-px border-b-2 px-1 py-2.5 mr-6 text-[13.5px] font-extrabold ${
        activa ? 'border-neutral-900 text-neutral-900' : 'border-transparent text-neutral-500'
      }`}
    >
      {children}
    </button>
  )
}

function ClasificacionABCXYZ() {
  const resumen = useResumenABCXYZ()
  const clasificacion = useClasificacionABCXYZ()
  const migraciones = useMigracionesABCXYZ()

  const celdas = useMemo(() => {
    const m = new Map(resumen.data?.map((c) => [c.celda, c]))
    return CLASES_ABC.flatMap((abc) => CLASES_XYZ.map((xyz) => m.get(`${abc}${xyz}`)))
  }, [resumen.data])

  return (
    <Estado cargando={resumen.isLoading || clasificacion.isLoading} error={resumen.error ?? clasificacion.error}>
      <div className="flex flex-col gap-5">
        <p className="text-[12.5px] font-semibold leading-snug text-neutral-500">
          <strong className="text-neutral-700">Prioridad</strong> (Alta/Media/Baja): qué tanto pesa el producto en
          las ventas. <strong className="text-neutral-700">Demanda</strong> (Estable/Variable/Irregular): qué tan
          predecible es mes a mes.
        </p>

        <div className="grid grid-cols-3 gap-3">
          {celdas.map((celda, i) => {
            const abc = CLASES_ABC[Math.floor(i / 3)]
            const xyz = CLASES_XYZ[i % 3]
            return (
              <div
                key={`${abc}${xyz}`}
                className={`flex flex-col gap-2 rounded-[14px] border p-4 ${COLOR_ABC[abc]}`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex flex-col">
                    <span className="text-sm font-extrabold">
                      {ETIQUETA_ABC[abc]} · {ETIQUETA_XYZ[xyz]}
                    </span>
                    <span className="text-[10px] font-bold uppercase tracking-wide opacity-60">{abc}{xyz}</span>
                  </div>
                  <span className="text-xs font-bold">{celda?.num_productos ?? 0} prod.</span>
                </div>
                <span className="text-lg font-extrabold tracking-tight">
                  {formatearLempiras(celda?.valor_consumo_total ?? 0)}
                </span>
                <p className="text-[11.5px] font-semibold leading-snug opacity-80">
                  {celda?.recomendacion ?? 'Sin productos en esta celda.'}
                </p>
              </div>
            )
          })}
        </div>

        <Estado
          cargando={false}
          error={null}
          vacio={clasificacion.data?.length === 0}
          mensajeVacio="No hay productos clasificados todavía."
        >
          <div className="overflow-hidden rounded-[14px] border border-neutral-200 bg-white">
            <table className="w-full text-sm">
              <thead className="bg-neutral-50 text-left text-[10.5px] font-extrabold uppercase tracking-wide text-neutral-500">
                <tr>
                  <th className="px-4 py-2.5">Código</th>
                  <th className="px-4 py-2.5">Nombre</th>
                  <th className="px-4 py-2.5 text-right">Valor de consumo</th>
                  <th className="px-4 py-2.5">Prioridad</th>
                  <th className="px-4 py-2.5">Demanda</th>
                  <th className="px-4 py-2.5 text-right">CV demanda</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-100">
                {clasificacion.data?.map((r) => (
                  <tr key={r.codigo}>
                    <td className="px-4 py-3 font-mono text-xs font-bold text-neutral-700">{r.codigo}</td>
                    <td className="px-4 py-3 text-[13px] font-bold text-neutral-900">{r.nombre}</td>
                    <td className="px-4 py-3 text-right text-[13px] font-bold text-neutral-900">
                      {formatearLempiras(r.valor_consumo)}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`rounded-full border px-2.5 py-1 text-xs font-extrabold ${COLOR_ABC[r.clase_abc]}`}>
                        {ETIQUETA_ABC[r.clase_abc]} ({r.clase_abc})
                      </span>
                    </td>
                    <td className="px-4 py-3 text-[13px] font-semibold text-neutral-600">
                      {ETIQUETA_XYZ[r.clase_xyz]} ({r.clase_xyz})
                    </td>
                    <td className="px-4 py-3 text-right text-[13px] font-semibold text-neutral-600">
                      {r.cv_demanda ?? '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Estado>

        <div className="overflow-hidden rounded-[14px] border border-neutral-200 bg-white">
          <div className="flex items-center justify-between border-b border-neutral-100 px-5 py-3.5">
            <div>
              <h2 className="text-sm font-extrabold text-neutral-900">Migraciones de celda</h2>
              <p className="text-xs font-semibold text-neutral-500">
                Productos que cambiaron de celda ABC-XYZ respecto al mes calendario anterior
                (ventana móvil de 12 meses; p. ej. AX → AZ es una alerta más fuerte que el corte transversal solo)
              </p>
            </div>
            <BotonFantasma
              onClick={() => descargarCSV('migraciones_abc_xyz', migraciones.data ?? [])}
              disabled={!migraciones.data?.length}
            >
              <IconoDescargar size={16} />
              Exportar CSV
            </BotonFantasma>
          </div>
          <Estado
            cargando={migraciones.isLoading}
            error={migraciones.error}
            vacio={migraciones.data?.length === 0}
            mensajeVacio="Sin cambios de celda detectados (hace falta más de 12 meses de historial para la primera comparación)."
          >
            <table className="w-full text-sm">
              <thead className="bg-neutral-50 text-left text-[10.5px] font-extrabold uppercase tracking-wide text-neutral-500">
                <tr>
                  <th className="px-5 py-2.5">Mes</th>
                  <th className="px-5 py-2.5">Código</th>
                  <th className="px-5 py-2.5">Nombre</th>
                  <th className="px-5 py-2.5">Cambio de celda</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-100">
                {migraciones.data?.map((m, i) => (
                  <tr key={`${m.mes}-${m.codigo}-${i}`}>
                    <td className="px-5 py-2.5 text-[13px] font-semibold text-neutral-600">{m.mes}</td>
                    <td className="px-5 py-2.5 font-mono text-xs font-bold text-neutral-700">{m.codigo}</td>
                    <td className="px-5 py-2.5 text-[13px] font-bold text-neutral-900">{m.nombre}</td>
                    <td className="px-5 py-2.5">
                      <div className="flex items-center gap-2">
                        <CeldaBadge celda={m.celda_anterior} />
                        <span className="text-neutral-400">→</span>
                        <CeldaBadge celda={m.celda_nueva} />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Estado>
        </div>
      </div>
    </Estado>
  )
}

function CeldaBadge({ celda }: { celda: string }) {
  const abc = celda[0] as ClaseABC
  return (
    <span className={`rounded-full border px-2 py-0.5 text-[11px] font-extrabold ${COLOR_ABC[abc]}`}>
      {celda}
    </span>
  )
}

type Alcance = 'categoria' | 'producto'

function PrediccionDemanda() {
  const [alcance, setAlcance] = useState<Alcance>('categoria')
  const categorias = useCategorias()
  const prioritarios = useProductosPrioritarios()

  const [idCategoria, setIdCategoria] = useState<number | null>(null)
  const [codigoProducto, setCodigoProducto] = useState<string | null>(null)
  const [n, setN] = useState(3)
  const [tiempoEntregaDias, setTiempoEntregaDias] = useState(7)

  const primeraCategoria = categorias.data?.[0]?.id ?? null
  const primerProducto = prioritarios.data?.[0] ?? null
  const categoriaActiva = idCategoria ?? primeraCategoria
  const productoActivo = codigoProducto ?? primerProducto

  const pronosticoCategoria = usePronosticoCategoria(alcance === 'categoria' ? categoriaActiva : null, { n })
  const pronosticoProducto = usePronosticoProducto(alcance === 'producto' ? productoActivo : null, {
    n,
    tiempoEntregaDias,
  })

  const resultado = alcance === 'categoria' ? pronosticoCategoria.data : pronosticoProducto.data
  const cargando = alcance === 'categoria' ? pronosticoCategoria.isLoading : pronosticoProducto.isLoading
  const error = alcance === 'categoria' ? pronosticoCategoria.error : pronosticoProducto.error

  const datosGrafico = useMemo(() => {
    if (!resultado) return []
    const historico = resultado.serie_historica.map((p, i) => ({
      mes: p.mes,
      real: p.unidades,
      pronostico: i === resultado.serie_historica.length - 1 ? p.unidades : undefined,
      banda: undefined as [number, number] | undefined,
    }))
    const futuro = resultado.meses_pronosticados.map((mes, i) => ({
      mes,
      real: undefined as number | undefined,
      pronostico: resultado.pronostico[i],
      banda: [
        resultado.intervalo_confianza[i].limite_inferior,
        resultado.intervalo_confianza[i].limite_superior,
      ] as [number, number],
    }))
    return [...historico, ...futuro]
  }, [resultado])

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-wrap items-end gap-4 rounded-[14px] border border-neutral-200 bg-white px-6 py-5">
        <Campo etiqueta="Alcance">
          <div className="flex gap-0.5 rounded-[9px] bg-neutral-100 p-[3px]">
            {(['categoria', 'producto'] as const).map((a) => (
              <button
                key={a}
                onClick={() => setAlcance(a)}
                className={`rounded-[7px] px-3.5 py-2 text-[12.5px] font-bold capitalize ${
                  alcance === a ? 'bg-white text-neutral-900 shadow-sm' : 'text-neutral-500'
                }`}
              >
                {a}
              </button>
            ))}
          </div>
        </Campo>

        {alcance === 'categoria' ? (
          <Campo etiqueta="Categoría">
            <select
              value={categoriaActiva ?? ''}
              onChange={(e) => setIdCategoria(Number(e.target.value))}
              className="w-[180px] rounded-[9px] border border-neutral-200 px-3 py-2 text-[13px] font-bold text-neutral-800"
            >
              {categorias.data?.map((c) => (
                <option key={c.id} value={c.id}>{c.nombre}</option>
              ))}
            </select>
          </Campo>
        ) : (
          <Campo etiqueta="Producto (clase A/X)">
            <select
              value={productoActivo ?? ''}
              onChange={(e) => setCodigoProducto(e.target.value)}
              className="w-[180px] rounded-[9px] border border-neutral-200 px-3 py-2 font-mono text-[13px] font-bold text-neutral-800"
            >
              {prioritarios.data?.map((codigo) => (
                <option key={codigo} value={codigo}>{codigo}</option>
              ))}
            </select>
          </Campo>
        )}

        <Campo etiqueta="Meses a pronosticar">
          <input
            type="number"
            min={1}
            max={12}
            value={n}
            onChange={(e) => setN(Math.max(1, Math.min(12, Number(e.target.value) || 1)))}
            className="w-[90px] rounded-[9px] border border-neutral-200 px-3 py-2 text-[13px] font-bold text-neutral-800"
          />
        </Campo>

        {alcance === 'producto' && (
          <Campo etiqueta="Tiempo de entrega (días)">
            <input
              type="number"
              min={1}
              max={90}
              value={tiempoEntregaDias}
              onChange={(e) => setTiempoEntregaDias(Math.max(1, Math.min(90, Number(e.target.value) || 1)))}
              className="w-[90px] rounded-[9px] border border-neutral-200 px-3 py-2 text-[13px] font-bold text-neutral-800"
            />
          </Campo>
        )}
      </div>

      {alcance === 'producto' && prioritarios.data?.length === 0 && (
        <p className="text-sm font-semibold text-neutral-500">
          Ningún producto quedó clasificado como A/X (alto valor y demanda estable) todavía.
        </p>
      )}

      <Estado
        cargando={cargando}
        error={error}
        vacio={!resultado}
      >
        {resultado && (
          <div className="flex flex-col gap-5">
            <div className="h-80 rounded-[14px] border border-neutral-200 bg-white p-6">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={datosGrafico}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e5e5" />
                  <XAxis dataKey="mes" fontSize={10.5} fontWeight={600} stroke="#a3a3a3" tickLine={false} />
                  <YAxis fontSize={11} stroke="#a3a3a3" tickLine={false} axisLine={false} />
                  <Tooltip
                    formatter={(valor: unknown, nombre: unknown) =>
                      Array.isArray(valor)
                        ? [`${valor[0]} – ${valor[1]} uds`, nombre as string]
                        : [valor as number, nombre as string]
                    }
                  />
                  <Legend wrapperStyle={{ fontSize: 12.5, fontWeight: 700 }} />
                  <Area
                    type="monotone"
                    dataKey="banda"
                    name="Banda de confianza (95%)"
                    stroke="none"
                    fill="#2a78d6"
                    fillOpacity={0.12}
                    isAnimationActive={false}
                  />
                  <Line type="monotone" dataKey="real" name="Demanda real" stroke="#171717" strokeWidth={2.25} dot={false} />
                  <Line
                    type="monotone"
                    dataKey="pronostico"
                    name="Pronóstico"
                    stroke="#2a78d6"
                    strokeWidth={2.25}
                    strokeDasharray="5 5"
                    dot={false}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>

            <div className="flex items-stretch gap-5">
              <div className="flex-1 overflow-hidden rounded-[14px] border border-neutral-200 bg-white">
                <div className="border-b border-neutral-100 px-5 py-3.5">
                  <h2 className="text-sm font-extrabold text-neutral-900">Comparación de modelos</h2>
                  <p className="text-xs font-semibold text-neutral-500">
                    Backtest sobre los últimos meses (MAE, MAPE y MASE, menor es mejor; MASE &lt; 1 supera al ingenuo)
                  </p>
                </div>
                <table className="w-full text-sm">
                  <thead className="text-left text-[10.5px] font-extrabold uppercase tracking-wide text-neutral-500">
                    <tr>
                      <th className="px-5 py-2">Modelo</th>
                      <th className="px-5 py-2 text-right">MAE</th>
                      <th className="px-5 py-2 text-right">MAPE</th>
                      <th className="px-5 py-2 text-right">MASE</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-neutral-100">
                    {resultado.comparacion_modelos.map((m: ComparacionModelo) => (
                      <tr key={m.modelo} className={m.modelo === resultado.mejor_modelo ? 'bg-emerald-50' : ''}>
                        <td className="px-5 py-2.5 text-[13px] font-bold text-neutral-800">
                          {NOMBRES_MODELO[m.modelo] ?? m.modelo}
                          {m.modelo === resultado.mejor_modelo && (
                            <span className="ml-2 rounded-full bg-emerald-600 px-2 py-0.5 text-[10px] font-extrabold text-white">
                              MEJOR
                            </span>
                          )}
                        </td>
                        <td className="px-5 py-2.5 text-right text-[13px] font-semibold text-neutral-700">{m.mae}</td>
                        <td className="px-5 py-2.5 text-right text-[13px] font-semibold text-neutral-700">
                          {m.mape !== null ? `${m.mape}%` : '—'}
                        </td>
                        <td className="px-5 py-2.5 text-right text-[13px] font-semibold text-neutral-700">
                          {m.mase ?? '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {'punto_reorden' in resultado && (
                <div className="w-[280px] flex-shrink-0 rounded-[14px] border border-neutral-200 bg-white p-5">
                  <h2 className="text-sm font-extrabold text-neutral-900">Punto de reorden</h2>
                  <p className="mb-3 text-xs font-semibold text-neutral-500">
                    Con {tiempoEntregaDias} días de entrega y 95% de nivel de servicio
                  </p>
                  <div className="flex flex-col gap-2.5">
                    <FilaDato etiqueta="Demanda diaria media" valor={`${resultado.demanda_diaria_media} uds`} />
                    <FilaDato etiqueta="Desviación diaria" valor={`${resultado.demanda_diaria_desviacion} uds`} />
                    <FilaDato etiqueta="Stock de seguridad" valor={`${resultado.stock_seguridad} uds`} />
                    <div className="mt-1 rounded-[9px] bg-neutral-900 px-3.5 py-3">
                      <div className="text-[11px] font-bold text-neutral-300">Punto de reorden</div>
                      <div className="text-xl font-extrabold text-white">{resultado.punto_reorden} uds</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </Estado>
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

function FilaDato({ etiqueta, valor }: { etiqueta: string; valor: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-xs font-semibold text-neutral-500">{etiqueta}</span>
      <span className="text-[13px] font-bold text-neutral-800">{valor}</span>
    </div>
  )
}
