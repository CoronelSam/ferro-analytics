import { useRef, useState, type DragEvent, type FormEvent } from 'react'
import { Cabecera } from '../componentes/Cabecera'
import { BotonPrimario } from '../componentes/Boton'
import { IconoAlerta, IconoCheck, IconoNube } from '../componentes/Icono'
import { useImportarCSV } from '../lib/consultas'
import type { EntidadImportable } from '../lib/tipos'

const ENTIDADES: { valor: EntidadImportable; etiqueta: string }[] = [
  { valor: 'categorias', etiqueta: 'categorias.csv' },
  { valor: 'productos', etiqueta: 'productos.csv' },
  { valor: 'movimientos', etiqueta: 'movimientos.csv' },
]

export function Importar() {
  const [entidad, setEntidad] = useState<EntidadImportable>('productos')
  const [archivo, setArchivo] = useState<File | null>(null)
  const [arrastrando, setArrastrando] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const mutacion = useImportarCSV()

  function alEnviar(e: FormEvent) {
    e.preventDefault()
    if (!archivo) return
    mutacion.mutate({ entidad, archivo })
  }

  function alSoltar(e: DragEvent<HTMLDivElement>) {
    e.preventDefault()
    setArrastrando(false)
    const f = e.dataTransfer.files?.[0]
    if (f) setArchivo(f)
  }

  return (
    <div className="flex flex-col">
      <Cabecera titulo="Importar datos (CSV)" subtitulo="Sube categorías, productos o movimientos desde el sistema de inventario." />

      <div className="grid grid-cols-2 gap-5 px-8 py-7">
        <form onSubmit={alEnviar} className="rounded-[14px] border border-neutral-200 bg-white p-6">
          <div className="mb-2.5 text-xs font-extrabold uppercase tracking-wide text-neutral-500">Tipo de archivo</div>
          <div className="mb-5 flex gap-2">
            {ENTIDADES.map((e) => (
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

        <div className="rounded-[14px] border border-neutral-200 bg-white p-6">
          {!mutacion.isSuccess ? (
            <p className="text-sm font-semibold text-neutral-400">El resultado de la importación aparecerá aquí.</p>
          ) : (
            <>
              <div className="mb-1 flex items-center gap-2.5">
                <IconoCheck size={18} className="text-emerald-700" />
                <span className="text-[14.5px] font-extrabold text-neutral-900">
                  {mutacion.data.aceptados} registro(s) de {mutacion.data.entidad} aceptados
                </span>
              </div>
              {mutacion.data.insertados !== null && (
                <div className="mb-4 ml-7 text-xs font-semibold text-neutral-500">
                  Insertados: {mutacion.data.insertados} · Actualizados: {mutacion.data.actualizados}
                </div>
              )}
              {mutacion.data.rechazados.length > 0 && (
                <>
                  <div className="mb-1 flex items-center gap-2">
                    <IconoAlerta size={16} className="text-amber-700" />
                    <span className="text-[13px] font-extrabold text-neutral-900">
                      {mutacion.data.rechazados.length} fila(s) rechazada(s)
                    </span>
                  </div>
                  <div>
                    {mutacion.data.rechazados.map((r) => (
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
      </div>
    </div>
  )
}
