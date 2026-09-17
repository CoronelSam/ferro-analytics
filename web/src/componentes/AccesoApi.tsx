// Indicador y control del modo solo lectura (ver api/seguridad.py,
// FERRO_API_KEY). Solo se muestra si el backend tiene esa variable
// configurada: en desarrollo normal (sin ella) no hay nada que mostrar.
import { useState } from 'react'
import { borrarClaveApi, guardarClaveApi, useClaveApiPresente } from '../lib/claveApi'
import { useSalud } from '../lib/consultas'
import { IconoCandado, IconoCandadoAbierto } from './Icono'

export function AccesoApi() {
  const salud = useSalud()
  const claveGuardada = useClaveApiPresente()
  const [editando, setEditando] = useState(false)
  const [valor, setValor] = useState('')

  if (!salud.data?.solo_lectura) return null

  function guardar() {
    if (!valor.trim()) return
    guardarClaveApi(valor.trim())
    setEditando(false)
    setValor('')
  }

  return (
    <div className="rounded-xl border border-[#DCE5EF] bg-[#F5F8FC] px-3 py-3">
      <div className="flex items-center gap-2">
        {claveGuardada ? (
          <IconoCandadoAbierto size={16} className="text-emerald-700" />
        ) : (
          <IconoCandado size={16} className="text-[#E65F00]" />
        )}
        <span className="text-[11px] font-extrabold uppercase tracking-wide text-[#53647A]">
          {claveGuardada ? 'Clave activa' : 'Solo lectura'}
        </span>
      </div>

      {!claveGuardada && !editando && (
        <button
          onClick={() => setEditando(true)}
          className="mt-1.5 text-[11px] font-bold text-[#124E96] underline underline-offset-2"
        >
          Ingresar clave de la API
        </button>
      )}

      {editando && (
        <div className="mt-2 flex flex-col gap-1.5">
          <input
            type="password"
            autoFocus
            value={valor}
            onChange={(e) => setValor(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && guardar()}
            placeholder="X-API-Key"
            className="w-full rounded-[7px] border border-[#DCE5EF] px-2.5 py-1.5 text-[12px] font-bold text-[#243B55]"
          />
          <div className="flex gap-1.5">
            <button
              onClick={guardar}
              className="flex-1 rounded-[7px] bg-[#124E96] px-2.5 py-1.5 text-[11px] font-extrabold text-white"
            >
              Guardar
            </button>
            <button
              onClick={() => {
                setEditando(false)
                setValor('')
              }}
              className="rounded-[7px] border border-[#DCE5EF] px-2.5 py-1.5 text-[11px] font-bold text-[#53647A]"
            >
              Cancelar
            </button>
          </div>
        </div>
      )}

      {claveGuardada && (
        <button
          onClick={borrarClaveApi}
          className="mt-1.5 text-[11px] font-bold text-[#53647A] underline underline-offset-2"
        >
          Quitar clave
        </button>
      )}

      <p className="mt-2 text-[10px] font-semibold leading-snug text-[#8A98AA]">
        {claveGuardada
          ? 'Puedes importar, sincronizar y deshacer lotes.'
          : 'Solo puedes consultar. Pide la clave a quien administra este dashboard para poder importar o modificar datos.'}
      </p>
    </div>
  )
}
