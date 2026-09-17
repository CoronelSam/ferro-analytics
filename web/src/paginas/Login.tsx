import { useState, type FormEvent } from 'react'
import { BotonPrimario } from '../componentes/Boton'
import { IconoCandado, IconoOjo, IconoOjoCerrado } from '../componentes/Icono'
import { ModoTema } from '../componentes/ModoTema'
import { useIniciarSesion } from '../lib/consultas'

export function Login() {
  const [usuario, setUsuario] = useState('')
  const [contrasena, setContrasena] = useState('')
  const [mostrarContrasena, setMostrarContrasena] = useState(false)
  const mutacion = useIniciarSesion()

  function alEnviar(e: FormEvent) {
    e.preventDefault()
    if (!usuario.trim() || !contrasena) return
    mutacion.mutate({ usuario: usuario.trim(), contrasena })
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center bg-[#F5F8FC] px-4">
      <div className="absolute right-5 top-5">
        <ModoTema compacto />
      </div>
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
            <div className="relative">
              <input
                type={mostrarContrasena ? 'text' : 'password'}
                autoComplete="current-password"
                value={contrasena}
                onChange={(e) => setContrasena(e.target.value)}
                className="w-full rounded-[9px] border border-[#DCE5EF] px-3 py-2.5 pr-11 text-[13.5px] font-bold text-[#243B55]"
              />
              <button
                type="button"
                onClick={() => setMostrarContrasena((valor) => !valor)}
                aria-label={mostrarContrasena ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                title={mostrarContrasena ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                className="fa-password-toggle absolute right-1.5 top-1/2 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-lg text-[#6D7B8F]"
              >
                {mostrarContrasena ? <IconoOjoCerrado size={18} /> : <IconoOjo size={18} />}
              </button>
            </div>
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
