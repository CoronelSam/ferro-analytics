import { useState } from 'react'
import { Estado } from '../componentes/Estado'
import { Cabecera } from '../componentes/Cabecera'
import { BotonFantasma } from '../componentes/Boton'
import { IconoDescargar } from '../componentes/Icono'
import { useAlertas } from '../lib/consultas'
import { descargarCSV } from '../lib/csv'

export function Alertas() {
  const [usarUmbral, setUsarUmbral] = useState(false)
  const [umbral, setUmbral] = useState(5)

  const alertas = useAlertas(usarUmbral ? umbral : null)

  return (
    <div className="flex flex-col">
      <Cabecera titulo="Alertas de stock bajo" subtitulo={`${alertas.data?.length ?? 0} productos requieren reposición.`}>
        <BotonFantasma
          onClick={() => descargarCSV('alertas_stock_bajo', alertas.data ?? [])}
          disabled={!alertas.data?.length}
        >
          <IconoDescargar size={16} />
          Exportar CSV
        </BotonFantasma>
      </Cabecera>

      <div className="flex flex-col gap-5 px-8 py-7">
        <div className="flex items-center gap-3.5 fa-card px-5 py-4">
          <button
            onClick={() => setUsarUmbral((v) => !v)}
            className={`relative h-[22px] w-[38px] flex-shrink-0 rounded-full transition-colors ${usarUmbral ? 'bg-[#124E96]' : 'bg-neutral-200'}`}
          >
            <span
              className={`absolute top-[3px] h-4 w-4 rounded-full bg-white shadow transition-transform ${
                usarUmbral ? 'translate-x-[19px]' : 'translate-x-[3px]'
              }`}
            />
          </button>
          <div className="flex-1">
            <div className="text-[13.5px] font-bold text-[#13233A]">Usar umbral fijo</div>
            <div className="text-xs font-semibold text-[#6D7B8F]">En vez del stock mínimo propio de cada producto</div>
          </div>
          <input
            type="number"
            min={0}
            value={umbral}
            onChange={(e) => setUmbral(Number(e.target.value))}
            disabled={!usarUmbral}
            className="w-20 rounded-[9px] border border-[#DCE5EF] bg-[#F5F8FC] px-3 py-2 text-[13px] font-bold text-[#243B55] disabled:text-[#8A98AA]"
          />
        </div>

        <Estado
          cargando={alertas.isLoading}
          error={alertas.error}
          vacio={alertas.data?.length === 0}
          mensajeVacio="Sin alertas: todo el stock está por encima del mínimo."
        >
          <div className="grid grid-cols-2 gap-4">
            {alertas.data?.map((a) => {
              const pct = Math.round((a.stock_actual / a.minimo) * 100)
              return (
                <div key={a.codigo} className="flex flex-col gap-3.5 rounded-[14px] border border-[#FFD9BF] bg-white p-5">
                  <div className="flex items-start justify-between gap-2.5">
                    <div className="min-w-0">
                      <div className="truncate text-sm font-extrabold text-[#13233A]">{a.nombre}</div>
                      <div className="mt-0.5 font-mono text-[11.5px] font-bold text-[#6D7B8F]">{a.codigo}</div>
                    </div>
                    <span className="flex-shrink-0 rounded-full bg-[#FFF7F1] px-2.5 py-1 text-xs font-extrabold text-[#E65F00]">
                      {a.diferencia} uds
                    </span>
                  </div>
                  <div>
                    <div className="h-2 overflow-hidden rounded-full bg-[#EDF3F9]">
                      <div className="h-full rounded-full bg-[#FF7A1A]" style={{ width: `${Math.min(100, pct)}%` }} />
                    </div>
                    <div className="mt-1.5 flex justify-between text-xs font-bold">
                      <span className="text-[#53647A]">
                        Actual: <span className="text-[#E65F00]">{a.stock_actual}</span>
                      </span>
                      <span className="text-[#6D7B8F]">Mínimo: {a.minimo}</span>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </Estado>
      </div>
    </div>
  )
}
