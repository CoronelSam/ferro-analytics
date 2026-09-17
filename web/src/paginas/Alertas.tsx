import { useMemo, useState } from 'react'
import { Estado } from '../componentes/Estado'
import { Cabecera } from '../componentes/Cabecera'
import { BotonFantasma } from '../componentes/Boton'
import { BadgeEstado } from '../componentes/BadgeEstado'
import { CategoriaBadge } from '../componentes/CategoriaBadge'
import { IconoChevronAbajo, IconoDescargar } from '../componentes/Icono'
import { useAlertas, useCategorias } from '../lib/consultas'
import { formatearLempiras } from '../lib/api'
import { descargarCSV } from '../lib/csv'
import type { AlertaStockBajo, Categoria } from '../lib/tipos'

type Nivel = AlertaStockBajo['nivel']

const NIVELES: Nivel[] = ['agotado', 'critico', 'bajo']

const ETIQUETA_NIVEL: Record<Nivel, string> = {
  agotado: 'Agotados',
  critico: 'Críticos',
  bajo: 'Bajo mínimo',
}

const DESCRIPCION_NIVEL: Record<Nivel, string> = {
  agotado: 'Sin unidades en stock ahora mismo.',
  critico: 'Stock en la mitad del mínimo o menos.',
  bajo: 'Por debajo del mínimo, pero por encima de la mitad.',
}

const COLOR_TARJETA_NIVEL: Record<Nivel, string> = {
  agotado: 'border-red-200 bg-red-50 text-red-800',
  critico: 'border-red-100 bg-red-50/60 text-red-700',
  bajo: 'border-orange-100 bg-orange-50/60 text-orange-700',
}

const COLOR_BORDE_TARJETA: Record<Nivel, string> = {
  agotado: 'border-red-200',
  critico: 'border-[#FFD9BF]',
  bajo: 'border-[#FFD9BF]',
}

const COLOR_BARRA: Record<Nivel, string> = {
  agotado: 'bg-red-600',
  critico: 'bg-[#E65F00]',
  bajo: 'bg-[#FF7A1A]',
}

function formatearDiasCobertura(dias: number | null): string {
  if (dias === null) return 'Sin ventas recientes'
  if (dias < 1) return '< 1 día'
  const redondeado = Math.round(dias)
  return `≈ ${redondeado} día${redondeado === 1 ? '' : 's'}`
}

export function Alertas() {
  const [usarUmbral, setUsarUmbral] = useState(false)
  const [umbral, setUmbral] = useState(5)
  const [categoriaFiltro, setCategoriaFiltro] = useState<number | null>(null)
  const [nivelFiltro, setNivelFiltro] = useState<Nivel | null>(null)

  const alertas = useAlertas(usarUmbral ? umbral : null)
  const categorias = useCategorias()

  const conteoPorNivel = useMemo(() => {
    const conteo: Record<Nivel, number> = { agotado: 0, critico: 0, bajo: 0 }
    for (const a of alertas.data ?? []) conteo[a.nivel]++
    return conteo
  }, [alertas.data])

  const valorTotalReposicion = useMemo(
    () => (alertas.data ?? []).reduce((acc, a) => acc + a.valor_reposicion, 0),
    [alertas.data],
  )

  const alertasFiltradas = useMemo(
    () =>
      (alertas.data ?? []).filter(
        (a) =>
          (categoriaFiltro === null || a.id_categoria === categoriaFiltro) &&
          (nivelFiltro === null || a.nivel === nivelFiltro),
      ),
    [alertas.data, categoriaFiltro, nivelFiltro],
  )

  const hayFiltroActivo = categoriaFiltro !== null || nivelFiltro !== null

  function alternarNivel(nivel: Nivel) {
    setNivelFiltro((actual) => (actual === nivel ? null : nivel))
  }

  return (
    <div className="flex flex-col">
      <Cabecera titulo="Alertas de stock bajo" subtitulo={`${alertas.data?.length ?? 0} productos requieren reposición.`}>
        <BotonFantasma
          onClick={() => descargarCSV('alertas_stock_bajo', alertasFiltradas)}
          disabled={!alertasFiltradas.length}
        >
          <IconoDescargar size={16} />
          Exportar CSV
        </BotonFantasma>
      </Cabecera>

      <div className="flex flex-col gap-5 px-8 py-7">
        <p className="text-[12.5px] font-semibold leading-snug text-neutral-500">
          Un producto aparece aquí cuando su stock actual está por debajo de su mínimo (o del umbral fijo, si lo
          activás abajo). <strong className="text-neutral-700">Agotado</strong> es stock en cero,{' '}
          <strong className="text-neutral-700">crítico</strong> es la mitad del mínimo o menos. La{' '}
          <strong className="text-neutral-700">cobertura</strong> estima cuántos días más dura el stock al ritmo de
          ventas de los últimos 60 días; no aparece si el producto no tuvo salidas recientes. Tocá una tarjeta de
          nivel para filtrar la lista.
        </p>

        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {NIVELES.map((nivel) => {
            const activa = nivelFiltro === nivel
            return (
              <button
                key={nivel}
                type="button"
                onClick={() => alternarNivel(nivel)}
                className={`flex flex-col gap-1.5 rounded-[14px] border p-4 text-left transition ${COLOR_TARJETA_NIVEL[nivel]} ${
                  activa
                    ? 'ring-2 ring-[#124E96] ring-offset-1'
                    : nivelFiltro
                      ? 'opacity-50 hover:opacity-80'
                      : 'hover:-translate-y-0.5 hover:shadow-sm'
                }`}
              >
                <span className="text-[11px] font-extrabold uppercase tracking-wide opacity-70">
                  {ETIQUETA_NIVEL[nivel]}
                </span>
                <span className="text-2xl font-extrabold tracking-tight">{conteoPorNivel[nivel]}</span>
                <span className="text-[11.5px] font-semibold leading-snug opacity-80">
                  {DESCRIPCION_NIVEL[nivel]}
                </span>
              </button>
            )
          })}

          <div className="flex flex-col gap-1.5 rounded-[14px] border border-[#DCE5EF] bg-white p-4">
            <span className="text-[11px] font-extrabold uppercase tracking-wide text-[#6D7B8F]">A reponer</span>
            <span
              className="text-2xl font-extrabold tracking-tight text-[#13233A]"
              title="Suma del costo estimado de cubrir el déficit de cada producto, al precio unitario actual."
            >
              {formatearLempiras(valorTotalReposicion)}
            </span>
            <span className="text-[11.5px] font-semibold leading-snug text-[#6D7B8F]">
              Costo estimado de cubrir todos los déficits.
            </span>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3.5 fa-card px-5 py-4">
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
            <div className="text-xs font-semibold text-[#6D7B8F]">
              En vez del stock mínimo propio de cada producto, considerar bajo a cualquiera por debajo de este número.
            </div>
          </div>
          <input
            type="number"
            min={0}
            value={umbral}
            onChange={(e) => setUmbral(Number(e.target.value))}
            disabled={!usarUmbral}
            className="w-20 rounded-[9px] border border-[#DCE5EF] bg-[#F5F8FC] px-3 py-2 text-[13px] font-bold text-[#243B55] disabled:text-[#8A98AA]"
          />

          <div className="h-8 w-px flex-shrink-0 bg-[#DCE5EF]" />

          <SelectorCategoria
            categorias={categorias.data ?? []}
            idCategoria={categoriaFiltro}
            onChange={setCategoriaFiltro}
          />
        </div>

        {hayFiltroActivo && (
          <div className="flex items-center gap-2.5 text-[12.5px] font-bold text-[#124E96]">
            <span>
              Mostrando {alertasFiltradas.length} de {alertas.data?.length ?? 0} producto
              {(alertas.data?.length ?? 0) === 1 ? '' : 's'}
            </span>
            <button
              onClick={() => {
                setCategoriaFiltro(null)
                setNivelFiltro(null)
              }}
              className="rounded-full bg-[#EDF3F9] px-2.5 py-1 text-[11px] font-extrabold hover:bg-[#DCE5EF]"
            >
              Quitar filtros ✕
            </button>
          </div>
        )}

        <Estado
          cargando={alertas.isLoading}
          error={alertas.error}
          vacio={alertasFiltradas.length === 0}
          mensajeVacio={
            hayFiltroActivo
              ? 'Ningún producto coincide con los filtros seleccionados.'
              : 'Sin alertas: todo el stock está por encima del mínimo.'
          }
        >
          <div className="grid grid-cols-2 gap-4">
            {alertasFiltradas.map((a) => {
              const pct = Math.round((a.stock_actual / a.minimo) * 100)
              return (
                <div
                  key={a.codigo}
                  className={`flex flex-col gap-3.5 rounded-[14px] border bg-white p-5 ${COLOR_BORDE_TARJETA[a.nivel]}`}
                >
                  <div className="flex items-start justify-between gap-2.5">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="truncate text-sm font-extrabold text-[#13233A]">{a.nombre}</span>
                        <BadgeEstado estado={a.nivel} />
                      </div>
                      <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
                        <span className="font-mono text-[11.5px] font-bold text-[#6D7B8F]">{a.codigo}</span>
                        <CategoriaBadge idCategoria={a.id_categoria} nombre={a.nombre_categoria} />
                      </div>
                    </div>
                    <span className="flex-shrink-0 rounded-full bg-[#FFF7F1] px-2.5 py-1 text-xs font-extrabold text-[#E65F00]">
                      {Math.abs(a.diferencia)} uds
                    </span>
                  </div>
                  <div>
                    <div className="h-2 overflow-hidden rounded-full bg-[#EDF3F9]">
                      <div
                        className={`h-full rounded-full ${COLOR_BARRA[a.nivel]}`}
                        style={{ width: `${Math.min(100, Math.max(0, pct))}%` }}
                      />
                    </div>
                    <div className="mt-1.5 flex justify-between text-xs font-bold">
                      <span className="text-[#53647A]">
                        Actual: <span className="text-[#E65F00]">{a.stock_actual}</span>
                      </span>
                      <span className="text-[#6D7B8F]">Mínimo: {a.minimo}</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between border-t border-[#F0F3F8] pt-3 text-xs font-bold">
                    <span
                      className="text-[#53647A]"
                      title="Estimado según el ritmo de ventas de los últimos 60 días; no se calcula si el producto no tuvo salidas recientes."
                    >
                      Cobertura: <span className="text-[#13233A]">{formatearDiasCobertura(a.dias_cobertura)}</span>
                    </span>
                    <span
                      className="text-[#53647A]"
                      title="Costo estimado de cubrir el déficit al precio unitario actual."
                    >
                      A reponer: <span className="text-[#13233A]">{formatearLempiras(a.valor_reposicion)}</span>
                    </span>
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
