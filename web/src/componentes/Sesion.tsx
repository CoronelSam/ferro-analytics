// Usuario con sesión activa en la barra lateral, con opción de cerrarla
// (ver lib/sesion.ts). App.tsx solo muestra el resto del dashboard cuando
// hay una sesión, así que este componente siempre tiene una que mostrar.
import { cerrarSesion, useSesion } from '../lib/sesion'
import { IconoCandadoAbierto } from './Icono'

export function Sesion() {
  const sesion = useSesion()
  if (!sesion) return null

  return (
    <div className="rounded-xl border border-[#DCE5EF] bg-[#F5F8FC] px-3 py-3">
      <div className="flex items-center gap-2">
        <IconoCandadoAbierto size={16} className="text-emerald-700" />
        <span className="truncate text-[12.5px] font-extrabold text-[#243B55]">{sesion.nombre}</span>
      </div>
      <button
        onClick={cerrarSesion}
        className="mt-1.5 text-[11px] font-bold text-[#53647A] underline underline-offset-2"
      >
        Cerrar sesión
      </button>
    </div>
  )
}
