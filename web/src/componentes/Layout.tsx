import { NavLink, Outlet } from 'react-router-dom'
import { Sesion } from './Sesion'
import { ModoTema } from './ModoTema'
import {
  IconoPanel,
  IconoInventario,
  IconoMovimientos,
  IconoReportes,
  IconoAnalitica,
  IconoAlertas,
  IconoImportar,
} from './Icono'
import { useAlertas } from '../lib/consultas'

const ENLACES = [
  { ruta: '/', etiqueta: 'Panel', Icono: IconoPanel },
  { ruta: '/inventario', etiqueta: 'Inventario', Icono: IconoInventario },
  { ruta: '/movimientos', etiqueta: 'Movimientos', Icono: IconoMovimientos },
  { ruta: '/reportes', etiqueta: 'Reportes', Icono: IconoReportes },
  { ruta: '/analitica', etiqueta: 'Analítica', Icono: IconoAnalitica },
  { ruta: '/alertas', etiqueta: 'Alertas', Icono: IconoAlertas },
  { ruta: '/importar', etiqueta: 'Importar', Icono: IconoImportar },
]

export function Layout() {
  const alertas = useAlertas(null)
  const numAlertas = alertas.data?.length ?? 0

  return (
    <div className="flex h-screen overflow-hidden bg-[#F5F8FC]">
      <aside className="flex h-screen w-[272px] flex-shrink-0 flex-col overflow-y-auto border-r border-[#DCE5EF] bg-white px-4 py-4 shadow-[6px_0_24px_rgba(11,46,89,0.035)]">
        <div className="mb-5 border-b border-[#E5ECF4] px-1 pb-5 pt-1">
          <img
            src="/ferroanalytics-logo.png"
            alt="FerroAnalytics"
            className="h-auto w-[205px] object-contain object-left"
          />
          <p className="mt-1 pl-1 text-[11px] font-bold tracking-[0.02em] text-[#6D7B8F]">
            Inventario y analítica inteligente
          </p>
        </div>

        <nav className="flex flex-col gap-1">
          {ENLACES.map(({ ruta, etiqueta, Icono }) => (
            <NavLink
              key={ruta}
              to={ruta}
              end={ruta === '/'}
              className={({ isActive }) =>
                `group flex items-center gap-3 rounded-xl px-3 py-2.5 text-[13.5px] font-bold transition-all ${
                  isActive
                    ? 'bg-[#124E96] text-white shadow-[0_8px_18px_rgba(18,78,150,0.18)]'
                    : 'text-[#53647A] hover:bg-[#EAF2FC] hover:text-[#124E96]'
                }`
              }
            >
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-current/0">
                <Icono size={19} />
              </span>
              <span className="flex-1">{etiqueta}</span>
              {etiqueta === 'Alertas' && numAlertas > 0 && (
                <span className="rounded-full bg-[#FF7A1A] px-2 py-1 text-[10.5px] font-extrabold leading-none text-white shadow-sm">
                  {numAlertas}
                </span>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="mt-auto flex flex-col gap-3">
          <ModoTema />
          <Sesion />
          <div className="rounded-xl border border-[#FFE0CC] bg-[#FFF7F1] px-3 py-3">
            <p className="text-[10px] font-extrabold uppercase tracking-[0.12em] text-[#E65F00]">FerroAnalytics</p>
            <p className="mt-1 text-[11px] font-semibold leading-relaxed text-[#6D7B8F]">
              Control visual, análisis y seguimiento del inventario.
            </p>
          </div>
        </div>
      </aside>

      <main className="h-screen min-w-0 flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}
