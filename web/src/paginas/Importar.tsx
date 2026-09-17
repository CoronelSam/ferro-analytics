import { useRef, useState, type DragEvent, type FormEvent } from 'react'
import { Cabecera } from '../componentes/Cabecera'
import { BotonPrimario } from '../componentes/Boton'
import { Estado } from '../componentes/Estado'
import { IconoAlerta, IconoCheck, IconoNube } from '../componentes/Icono'
import {
  useDeshacerLoteMovimientos,
  useEstadoImportacionBD,
  useImportarCSV,
  useImportarDesdeBD,
  useLotesMovimientos,
} from '../lib/consultas'
import type { EntidadImportable, LoteMovimientos, ResultadoImportacion } from '../lib/tipos'

const ENTIDADES_CSV: { valor: EntidadImportable; etiqueta: string }[] = [
  { valor: 'categorias', etiqueta: 'categorias.csv' },
  { valor: 'productos', etiqueta: 'productos.csv' },
  { valor: 'movimientos', etiqueta: 'movimientos.csv' },
]

const ENTIDADES_BD: { valor: EntidadImportable; etiqueta: string }[] = [
  { valor: 'categorias', etiqueta: 'Categorías' },
  { valor: 'productos', etiqueta: 'Productos' },
  { valor: 'movimientos', etiqueta: 'Movimientos' },
]

type Origen = 'csv' | 'bd' | 'deshacer'

const PESTANAS: { valor: Origen; etiqueta: string }[] = [
  { valor: 'csv', etiqueta: 'Archivo CSV' },
  { valor: 'bd', etiqueta: 'Base de datos' },
  { valor: 'deshacer', etiqueta: 'Deshacer' },
]

export function Importar() {
  const [origen, setOrigen] = useState<Origen>('csv')
  const [resultado, setResultado] = useState<ResultadoImportacion | null>(null)

  return (
    <div className="flex flex-col">
      <Cabecera titulo="Importar datos" subtitulo="Sube categorías, productos o movimientos desde el sistema de inventario." />

      <div className="px-8 py-7">
        <div className="mb-5 flex w-fit gap-0.5 rounded-[9px] bg-neutral-100 p-[3px]">
          {PESTANAS.map((p) => (
            <button
              key={p.valor}
              onClick={() => setOrigen(p.valor)}
              className={`rounded-[7px] px-4 py-2 text-[12.5px] font-bold ${
                origen === p.valor ? 'bg-white text-neutral-900 shadow-sm' : 'text-neutral-500'
              }`}
            >
              {p.etiqueta}
            </button>
          ))}
        </div>

        {origen === 'deshacer' ? (
          <DeshacerLotes />
        ) : (
          <div className="grid grid-cols-2 gap-5">
            {origen === 'csv' ? <ImportarCSV onResultado={setResultado} /> : <ImportarBD onResultado={setResultado} />}
            <PanelResultado resultado={resultado} />
          </div>
        )}
      </div>
    </div>
  )
}

function ImportarCSV({ onResultado }: { onResultado: (r: ResultadoImportacion) => void }) {
  const [entidad, setEntidad] = useState<EntidadImportable>('productos')
  const [archivo, setArchivo] = useState<File | null>(null)
  const [arrastrando, setArrastrando] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const mutacion = useImportarCSV()

  function alEnviar(e: FormEvent) {
    e.preventDefault()
    if (!archivo) return
    mutacion.mutate({ entidad, archivo }, { onSuccess: onResultado })
  }

  function alSoltar(e: DragEvent<HTMLDivElement>) {
    e.preventDefault()
    setArrastrando(false)
    const f = e.dataTransfer.files?.[0]
    if (f) setArchivo(f)
  }

  return (
    <form onSubmit={alEnviar} className="rounded-[14px] border border-neutral-200 bg-white p-6">
      <div className="mb-2.5 text-xs font-extrabold uppercase tracking-wide text-neutral-500">Tipo de archivo</div>
      <div className="mb-5 flex gap-2">
        {ENTIDADES_CSV.map((e) => (
          <button
            key={e.valor}
            type="button"
            onClick={() => setEntidad(e.valor)}
            className={`flex-1 rounded-[9px] border px-3 py-2.5 font-mono text-xs font-extrabold ${
              entidad === e.valor ? 'border-neutral-900 bg-neutral-900 text-white' : 'border-neutral-200 bg-white text-neutral-700'
            }`}
          >
            {e.etiqueta}
          </button>
        ))}
      </div>

      <div
        onDragOver={(e) => {
          e.preventDefault()
          setArrastrando(true)
        }}
        onDragLeave={() => setArrastrando(false)}
        onDrop={alSoltar}
        onClick={() => inputRef.current?.click()}
        className={`flex cursor-pointer flex-col items-center gap-2.5 rounded-xl border-[1.5px] border-dashed px-5 py-9 text-center ${
          arrastrando ? 'border-neutral-500 bg-neutral-100' : 'border-neutral-300 bg-neutral-50'
        }`}
      >
        <IconoNube size={40} className="text-neutral-400" />
        <div className="text-[13.5px] font-bold text-neutral-800">
          {archivo ? archivo.name : 'Arrastra tu CSV aquí'}
        </div>
        <div className="text-xs font-semibold text-neutral-500">
          {archivo ? 'Haz clic para cambiar de archivo' : 'o haz clic para seleccionar · formato .csv'}
        </div>
        <input
          ref={inputRef}
          type="file"
          accept=".csv"
          className="hidden"
          onChange={(e) => setArchivo(e.target.files?.[0] ?? null)}
        />
      </div>

      <div className="mt-5">
        <BotonPrimario type="submit" disabled={!archivo || mutacion.isPending}>
          {mutacion.isPending ? 'Importando...' : 'Importar archivo'}
        </BotonPrimario>
      </div>

      {mutacion.isError && <p className="mt-3 text-sm font-semibold text-red-600">Error: {mutacion.error.message}</p>}
    </form>
  )
}

function ImportarBD({ onResultado }: { onResultado: (r: ResultadoImportacion) => void }) {
  const [entidad, setEntidad] = useState<EntidadImportable>('productos')
  const estado = useEstadoImportacionBD()
  const mutacion = useImportarDesdeBD()

  function sincronizar() {
    mutacion.mutate(entidad, { onSuccess: onResultado })
  }

  return (
    <div className="rounded-[14px] border border-neutral-200 bg-white p-6">
      <div className="mb-2.5 text-xs font-extrabold uppercase tracking-wide text-neutral-500">Tipo de dato</div>
      <div className="mb-5 flex gap-2">
        {ENTIDADES_BD.map((e) => (
          <button
            key={e.valor}
            type="button"
            onClick={() => setEntidad(e.valor)}
            className={`flex-1 rounded-[9px] border px-3 py-2.5 text-xs font-extrabold ${
              entidad === e.valor ? 'border-neutral-900 bg-neutral-900 text-white' : 'border-neutral-200 bg-white text-neutral-700'
            }`}
          >
            {e.etiqueta}
          </button>
        ))}
      </div>

      {estado.isLoading ? (
        <p className="text-sm font-semibold text-neutral-400">Comprobando conexión...</p>
      ) : !estado.data?.disponible ? (
        <div className="flex flex-col items-center gap-2.5 rounded-xl border-[1.5px] border-dashed border-neutral-300 bg-neutral-50 px-5 py-9 text-center">
          <IconoAlerta size={28} className="text-neutral-400" />
          <div className="text-[13.5px] font-bold text-neutral-800">Sin base de datos configurada</div>
          <div className="max-w-xs text-xs font-semibold text-neutral-500">
            {estado.data?.detalle ?? 'Defina FERRO_BD_URL en el servidor de la API (Postgres o MySQL) para habilitar la sincronización.'}
          </div>
        </div>
      ) : (
        <div className="flex flex-col items-center gap-2 rounded-xl border-[1.5px] border-neutral-200 bg-neutral-50 px-5 py-9 text-center">
          <div className="flex items-center gap-1.5 text-xs font-extrabold text-emerald-700">
            <IconoCheck size={14} /> Conectado a {estado.data.motor}
          </div>
          <div className="max-w-xs text-xs font-semibold text-neutral-500">
            Trae {ENTIDADES_BD.find((e) => e.valor === entidad)?.etiqueta.toLowerCase()} directamente de la base de
            datos. Los movimientos se sincronizan de forma incremental: solo los posteriores al último ya importado.
          </div>
        </div>
      )}

      <div className="mt-5">
        <BotonPrimario onClick={sincronizar} disabled={!estado.data?.disponible || mutacion.isPending}>
          {mutacion.isPending ? 'Sincronizando...' : 'Sincronizar ahora'}
        </BotonPrimario>
      </div>

      {mutacion.isError && <p className="mt-3 text-sm font-semibold text-red-600">Error: {mutacion.error.message}</p>}
    </div>
  )
}

function PanelResultado({ resultado }: { resultado: ResultadoImportacion | null }) {
  return (
    <div className="rounded-[14px] border border-neutral-200 bg-white p-6">
      {!resultado ? (
        <p className="text-sm font-semibold text-neutral-400">El resultado de la importación aparecerá aquí.</p>
      ) : (
        <>
          <div className="mb-1 flex items-center gap-2.5">
            <IconoCheck size={18} className="text-emerald-700" />
            <span className="text-[14.5px] font-extrabold text-neutral-900">
              {resultado.aceptados} registro(s) de {resultado.entidad} aceptados
            </span>
          </div>
          {resultado.insertados !== null && (
            <div className="mb-4 ml-7 text-xs font-semibold text-neutral-500">
              Insertados: {resultado.insertados} · Actualizados: {resultado.actualizados}
            </div>
          )}
          {resultado.lote && (
            <div className="mb-4 ml-7 text-xs font-semibold text-neutral-500">
              Lote: <span className="font-mono text-neutral-700">{resultado.lote}</span> · para deshacerlo, pestaña
              "Deshacer"
            </div>
          )}
          {resultado.rechazados.length > 0 && (
            <>
              <div className="mb-1 flex items-center gap-2">
                <IconoAlerta size={16} className="text-amber-700" />
                <span className="text-[13px] font-extrabold text-neutral-900">
                  {resultado.rechazados.length} fila(s) rechazada(s)
                </span>
              </div>
              <div>
                {resultado.rechazados.map((r) => (
                  <div key={r.fila} className="flex gap-2.5 border-b border-neutral-100 py-2.5 last:border-0">
                    <IconoAlerta size={15} className="mt-0.5 flex-shrink-0 text-amber-700" />
                    <div>
                      <div className="text-[12.5px] font-bold text-neutral-800">Fila {r.fila}</div>
                      <div className="text-xs font-medium text-neutral-500">{r.motivo}</div>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </>
      )}
    </div>
  )
}

function DeshacerLotes() {
  const lotes = useLotesMovimientos()
  const mutacion = useDeshacerLoteMovimientos()
  const [loteEnProceso, setLoteEnProceso] = useState<string | null>(null)

  function deshacer(lote: LoteMovimientos) {
    const confirmado = window.confirm(
      `¿Eliminar ${lote.cantidad} movimiento(s) del lote "${lote.lote}"?\n\nEsta acción no se puede deshacer.`,
    )
    if (!confirmado) return
    setLoteEnProceso(lote.lote)
    mutacion.mutate(lote.lote, { onSettled: () => setLoteEnProceso(null) })
  }

  return (
    <div className="overflow-hidden rounded-[14px] border border-neutral-200 bg-white">
      <div className="border-b border-neutral-100 px-6 py-4">
        <h2 className="text-sm font-extrabold text-neutral-900">Deshacer una importación de movimientos</h2>
        <p className="text-xs font-semibold text-neutral-500">
          Elimina todos los movimientos de un lote (CSV o base de datos). No afecta a categorías ni productos.
        </p>
      </div>

      <Estado
        cargando={lotes.isLoading}
        error={lotes.error}
        vacio={lotes.data?.length === 0}
        mensajeVacio="No hay ninguna importación de movimientos identificada por lote."
      >
        <table className="w-full text-sm">
          <thead className="bg-neutral-50 text-left text-[10.5px] font-extrabold uppercase tracking-wide text-neutral-500">
            <tr>
              <th className="px-5 py-2.5">Lote</th>
              <th className="px-5 py-2.5 text-right">Cantidad</th>
              <th className="px-5 py-2.5">Desde</th>
              <th className="px-5 py-2.5">Hasta</th>
              <th className="px-5 py-2.5" />
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-100">
            {lotes.data?.map((l) => (
              <tr key={l.lote}>
                <td className="px-5 py-3 font-mono text-xs font-bold text-neutral-700">{l.lote}</td>
                <td className="px-5 py-3 text-right text-[13px] font-bold text-neutral-900">{l.cantidad}</td>
                <td className="px-5 py-3 text-[12.5px] font-semibold text-neutral-500">{l.fecha_desde}</td>
                <td className="px-5 py-3 text-[12.5px] font-semibold text-neutral-500">{l.fecha_hasta}</td>
                <td className="px-5 py-3 text-right">
                  <button
                    onClick={() => deshacer(l)}
                    disabled={loteEnProceso === l.lote}
                    className="rounded-[7px] border border-red-200 bg-red-50 px-3 py-1.5 text-xs font-extrabold text-red-700 disabled:opacity-40"
                  >
                    {loteEnProceso === l.lote ? 'Eliminando...' : 'Deshacer'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Estado>

      {mutacion.isError && (
        <p className="px-6 pb-4 text-sm font-semibold text-red-600">Error: {mutacion.error.message}</p>
      )}
    </div>
  )
}
