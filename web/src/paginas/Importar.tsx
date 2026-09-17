import { useEffect, useRef, useState, type DragEvent, type FormEvent } from 'react'
import { Cabecera } from '../componentes/Cabecera'
import { BotonFantasma, BotonPrimario } from '../componentes/Boton'
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
        <div className="mb-5 flex w-fit gap-0.5 rounded-[9px] bg-[#EDF3F9] p-[3px]">
          {PESTANAS.map((p) => (
            <button
              key={p.valor}
              onClick={() => setOrigen(p.valor)}
              className={`rounded-[7px] px-4 py-2 text-[12.5px] font-bold ${
                origen === p.valor ? 'bg-white text-[#13233A] shadow-sm' : 'text-[#6D7B8F]'
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
            {origen === 'csv' ? (
              <ImportarCSV onResultado={setResultado} />
            ) : (
              <ImportarBD onResultado={setResultado} />
            )}
            <PanelResultado resultado={resultado} />
          </div>
        )}
      </div>
    </div>
  )
}

function ImportarCSV({
  onResultado,
}: {
  onResultado: (r: ResultadoImportacion) => void
}) {
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
    <form onSubmit={alEnviar} className="fa-card p-6">
      <div className="mb-2.5 text-xs font-extrabold uppercase tracking-wide text-[#6D7B8F]">Tipo de archivo</div>
      <div className="mb-5 flex gap-2">
        {ENTIDADES_CSV.map((e) => (
          <button
            key={e.valor}
            type="button"
            onClick={() => setEntidad(e.valor)}
            className={`flex-1 rounded-[9px] border px-3 py-2.5 font-mono text-xs font-extrabold ${
              entidad === e.valor ? 'border-[#124E96] bg-[#124E96] text-white' : 'border-[#DCE5EF] bg-white text-[#3E536C]'
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
          arrastrando ? 'border-neutral-500 bg-[#EDF3F9]' : 'border-[#C9D7E6] bg-[#F5F8FC]'
        }`}
      >
        <IconoNube size={40} className="text-[#8A98AA]" />
        <div className="text-[13.5px] font-bold text-[#243B55]">
          {archivo ? archivo.name : 'Arrastra tu CSV aquí'}
        </div>
        <div className="text-xs font-semibold text-[#6D7B8F]">
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

function ImportarBD({
  onResultado,
}: {
  onResultado: (r: ResultadoImportacion) => void
}) {
  const [entidad, setEntidad] = useState<EntidadImportable>('productos')
  const estado = useEstadoImportacionBD()
  const mutacion = useImportarDesdeBD()

  function sincronizar() {
    mutacion.mutate(entidad, { onSuccess: onResultado })
  }

  return (
    <div className="fa-card p-6">
      <div className="mb-2.5 text-xs font-extrabold uppercase tracking-wide text-[#6D7B8F]">Tipo de dato</div>
      <div className="mb-5 flex gap-2">
        {ENTIDADES_BD.map((e) => (
          <button
            key={e.valor}
            type="button"
            onClick={() => setEntidad(e.valor)}
            className={`flex-1 rounded-[9px] border px-3 py-2.5 text-xs font-extrabold ${
              entidad === e.valor ? 'border-[#124E96] bg-[#124E96] text-white' : 'border-[#DCE5EF] bg-white text-[#3E536C]'
            }`}
          >
            {e.etiqueta}
          </button>
        ))}
      </div>

      {estado.isLoading ? (
        <p className="text-sm font-semibold text-[#8A98AA]">Comprobando conexión...</p>
      ) : !estado.data?.disponible ? (
        <div className="flex flex-col items-center gap-2.5 rounded-xl border-[1.5px] border-dashed border-[#C9D7E6] bg-[#F5F8FC] px-5 py-9 text-center">
          <IconoAlerta size={28} className="text-[#8A98AA]" />
          <div className="text-[13.5px] font-bold text-[#243B55]">Sin base de datos configurada</div>
          <div className="max-w-xs text-xs font-semibold text-[#6D7B8F]">
            {estado.data?.detalle ?? 'Defina FERRO_BD_URL en el servidor de la API (Postgres o MySQL) para habilitar la sincronización.'}
          </div>
        </div>
      ) : (
        <div className="flex flex-col items-center gap-2 rounded-xl border-[1.5px] border-[#DCE5EF] bg-[#F5F8FC] px-5 py-9 text-center">
          <div className="flex items-center gap-1.5 text-xs font-extrabold text-emerald-700">
            <IconoCheck size={14} /> Conectado a {estado.data.motor}
          </div>
          <div className="max-w-xs text-xs font-semibold text-[#6D7B8F]">
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
    <div className="fa-card p-6">
      {!resultado ? (
        <p className="text-sm font-semibold text-[#8A98AA]">El resultado de la importación aparecerá aquí.</p>
      ) : (
        <>
          <div className="mb-1 flex items-center gap-2.5">
            <IconoCheck size={18} className="text-emerald-700" />
            <span className="text-[14.5px] font-extrabold text-[#13233A]">
              {resultado.aceptados} registro(s) de {resultado.entidad} aceptados
            </span>
          </div>
          {resultado.insertados !== null && (
            <div className="mb-4 ml-7 text-xs font-semibold text-[#6D7B8F]">
              Insertados: {resultado.insertados} · Actualizados: {resultado.actualizados}
            </div>
          )}
          {resultado.lote && (
            <div className="mb-4 ml-7 text-xs font-semibold text-[#6D7B8F]">
              Lote: <span className="font-mono text-[#3E536C]">{resultado.lote}</span> · para deshacerlo, pestaña
              "Deshacer"
            </div>
          )}
          {resultado.rechazados.length > 0 && (
            <>
              <div className="mb-1 flex items-center gap-2">
                <IconoAlerta size={16} className="text-amber-700" />
                <span className="text-[13px] font-extrabold text-[#13233A]">
                  {resultado.rechazados.length} fila(s) rechazada(s)
                </span>
              </div>
              <div>
                {resultado.rechazados.map((r) => (
                  <div key={r.fila} className="flex gap-2.5 border-b border-[#EDF2F7] py-2.5 last:border-0">
                    <IconoAlerta size={15} className="mt-0.5 flex-shrink-0 text-amber-700" />
                    <div>
                      <div className="text-[12.5px] font-bold text-[#243B55]">Fila {r.fila}</div>
                      <div className="text-xs font-medium text-[#6D7B8F]">{r.motivo}</div>
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
  const [loteAConfirmar, setLoteAConfirmar] = useState<LoteMovimientos | null>(null)

  function confirmarDeshacer() {
    if (!loteAConfirmar) return
    const lote = loteAConfirmar
    setLoteAConfirmar(null)
    setLoteEnProceso(lote.lote)
    mutacion.mutate(lote.lote, { onSettled: () => setLoteEnProceso(null) })
  }

  return (
    <div className="fa-table-wrap">
      <div className="border-b border-[#EDF2F7] px-6 py-4">
        <h2 className="text-sm font-extrabold text-[#13233A]">Deshacer una importación de movimientos</h2>
        <p className="text-xs font-semibold text-[#6D7B8F]">
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
          <thead className="bg-[#F5F8FC] text-left text-[10.5px] font-extrabold uppercase tracking-wide text-[#6D7B8F]">
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
                <td className="px-5 py-3 font-mono text-xs font-bold text-[#3E536C]">{l.lote}</td>
                <td className="px-5 py-3 text-right text-[13px] font-bold text-[#13233A]">{l.cantidad}</td>
                <td className="px-5 py-3 text-[12.5px] font-semibold text-[#6D7B8F]">{l.fecha_desde}</td>
                <td className="px-5 py-3 text-[12.5px] font-semibold text-[#6D7B8F]">{l.fecha_hasta}</td>
                <td className="px-5 py-3 text-right">
                  <button
                    onClick={() => setLoteAConfirmar(l)}
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

      {loteAConfirmar && (
        <ModalConfirmarDeshacer
          lote={loteAConfirmar}
          onCancelar={() => setLoteAConfirmar(null)}
          onConfirmar={confirmarDeshacer}
        />
      )}
    </div>
  )
}

function ModalConfirmarDeshacer({
  lote,
  onCancelar,
  onConfirmar,
}: {
  lote: LoteMovimientos
  onCancelar: () => void
  onConfirmar: () => void
}) {
  useEffect(() => {
    function alTeclear(e: KeyboardEvent) {
      if (e.key === 'Escape') onCancelar()
    }
    window.addEventListener('keydown', alTeclear)
    return () => window.removeEventListener('keydown', alTeclear)
  }, [onCancelar])

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-[#0B1B2E]/45 px-4"
      onClick={onCancelar}
    >
      <div
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="titulo-confirmar-deshacer"
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-md rounded-2xl bg-white p-6 shadow-[0_24px_60px_rgba(11,27,46,0.28)]"
      >
        <div className="mb-4 flex items-start gap-3">
          <span className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl bg-red-50 text-red-600">
            <IconoAlerta size={20} />
          </span>
          <div>
            <h3 id="titulo-confirmar-deshacer" className="text-[15px] font-extrabold text-[#13233A]">
              Eliminar lote de movimientos
            </h3>
            <p className="mt-0.5 text-xs font-semibold text-[#6D7B8F]">
              Lote <span className="font-mono text-[#3E536C]">{lote.lote}</span> · {lote.fecha_desde} – {lote.fecha_hasta}
            </p>
          </div>
        </div>

        <div className="mb-5 flex flex-col gap-2.5 rounded-xl border border-red-100 bg-red-50/60 px-4 py-3.5 text-[12.5px] font-semibold leading-relaxed text-red-800">
          <p>
            Se eliminarán permanentemente <strong>{lote.cantidad} movimiento(s)</strong>. Esta acción no se puede
            deshacer.
          </p>
          <p>
            Los reportes y la analítica calculados a partir de movimientos (ventas mensuales, top inmovilizado,
            clasificación ABC-XYZ, predicción de demanda) cambiarán al recalcularse sin estos datos.
          </p>
          <p className="text-red-700/80">
            No afecta el stock actual ni los datos de productos o categorías: eso solo cambia al volver a
            importarlos.
          </p>
        </div>

        <div className="flex justify-end gap-2.5">
          <BotonFantasma onClick={onCancelar}>Cancelar</BotonFantasma>
          <button
            onClick={onConfirmar}
            className="flex items-center gap-1.5 whitespace-nowrap rounded-[10px] bg-red-600 px-4 py-2.5 text-[13.5px] font-extrabold text-white shadow-[0_6px_14px_rgba(220,38,38,0.25)] hover:bg-red-700 hover:-translate-y-px"
          >
            Eliminar lote
          </button>
        </div>
      </div>
    </div>
  )
}
