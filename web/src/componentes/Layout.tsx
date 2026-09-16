import { NavLink, Outlet } from 'react-router-dom'
import {
  IconoPanel,
  IconoInventario,
  IconoMovimientos,
  IconoReportes,
  IconoAlertas,
  IconoImportar,
} from './Icono'
import { useAlertas } from '../lib/consultas'

const ENLACES = [
  { ruta: '/', etiqueta: 'Panel', Icono: IconoPanel },
  { ruta: '/inventario', etiqueta: 'Inventario', Icono: IconoInventario },
  { ruta: '/movimientos', etiqueta: 'Movimientos', Icono: IconoMovimientos },
  { ruta: '/reportes', etiqueta: 'Reportes', Icono: IconoReportes },
  { ruta: '/alertas', etiqueta: 'Alertas', Icono: IconoAlertas },
  { ruta: '/importar', etiqueta: 'Importar', Icono: IconoImportar },
]

export function Layout() {
  const alertas = useAlertas(null)
  const numAlertas = alertas.data?.length ?? 0

  return (
    <div className="flex min-h-screen bg-neutral-50">
      <aside className="flex w-[260px] flex-shrink-0 flex-col border-r border-neutral-200 bg-white p-3.5">
        <div className="flex items-center gap-2.5 px-2 pb-5 pt-1">
          <div className="flex h-8 w-8 items-center justify-center rounded-[9px] bg-neutral-900 text-[15px] font-extrabold text-white">
            F
          </div>
          <div className="flex flex-col leading-tight">
            <span className="text-sm font-extrabold text-neutral-900">FerroAnalytics</span>
            <span className="text-[11px] font-semibold text-neutral-500">Analítica de inventario</span>
          </div>
        </div>

        <nav className="flex flex-col gap-0.5">
          {ENLACES.map(({ ruta, etiqueta, Icono }) => (
            <NavLink
              key={ruta}
              to={ruta}
              end={ruta === '/'}
              className={({ isActive }) =>
                `flex items-center gap-2.5 rounded-[9px] px-2.5 py-2.5 text-[13.5px] font-bold transition-colors ${
                  isActive ? 'bg-neutral-900 text-white' : 'text-neutral-600 hover:bg-neutral-100'
                }`
              }
            >
              <Icono size={19} />
              <span className="flex-1">{etiqueta}</span>
              {etiqueta === 'Alertas' && numAlertas > 0 && (
                <span className="rounded-full bg-red-600 px-1.5 py-0.5 text-[11px] font-bold leading-none text-white">
                  {numAlertas}
                </span>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="mt-auto border-t border-neutral-200 px-2.5 pb-1 pt-3.5">
          <span className="text-[10.5px] font-bold tracking-wide text-neutral-400">FASE II · API + WEB</span>
        </div>
      </aside>

      <main className="min-w-0 flex-1">
        <Outlet />
      </main>
    </div>
  )
}
