import { useState, type FormEvent } from 'react'
import { BotonPrimario } from '../componentes/Boton'
import { IconoCandado } from '../componentes/Icono'
import { useIniciarSesion } from '../lib/consultas'

export function Login() {
  const [usuario, setUsuario] = useState('')
  const [contrasena, setContrasena] = useState('')
  const mutacion = useIniciarSesion()

  function alEnviar(e: FormEvent) {
    e.preventDefault()
    if (!usuario.trim() || !contrasena) return
    mutacion.mutate({ usuario: usuario.trim(), contrasena })
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#F5F8FC] px-4">
      <div className="w-full max-w-[380px]">
        <div className="mb-6 flex flex-col items-center gap-1">
          <img
            src="/ferroanalytics-logo.png"
            alt="FerroAnalytics"
            className="h-auto w-[220px] object-contain"
          />
          <p className="text-[12px] font-bold tracking-[0.02em] text-[#6D7B8F]">
            Inventario y analítica inteligente
          </p>
        </div>

        <form onSubmit={alEnviar} className="fa-card p-7">
          <div className="mb-5 flex items-center gap-2">
            <IconoCandado size={17} className="text-[#124E96]" />
            <h1 className="text-[15px] font-extrabold text-[#13233A]">Iniciar sesión</h1>
          </div>

          <label className="mb-3 block">
            <span className="mb-1.5 block text-[11px] font-extrabold uppercase tracking-wide text-[#6D7B8F]">
              Usuario
            </span>
            <input
              autoFocus
              autoComplete="username"
              value={usuario}
              onChange={(e) => setUsuario(e.target.value)}
              className="w-full rounded-[9px] border border-[#DCE5EF] px-3 py-2.5 text-[13.5px] font-bold text-[#243B55]"
            />
          </label>

          <label className="mb-5 block">
            <span className="mb-1.5 block text-[11px] font-extrabold uppercase tracking-wide text-[#6D7B8F]">
              Contraseña
            </span>
            <input
              type="password"
              autoComplete="current-password"
              value={contrasena}
              onChange={(e) => setContrasena(e.target.value)}
              className="w-full rounded-[9px] border border-[#DCE5EF] px-3 py-2.5 text-[13.5px] font-bold text-[#243B55]"
            />
          </label>

          {mutacion.isError && (
            <p className="mb-4 text-[12.5px] font-semibold text-red-600">{mutacion.error.message}</p>
          )}

          <BotonPrimario type="submit" disabled={mutacion.isPending}>
            {mutacion.isPending ? 'Ingresando...' : 'Ingresar'}
          </BotonPrimario>
        </form>
      </div>
    </div>
  )
}
