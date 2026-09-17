import { useState } from 'react'

const CLAVE_TEMA = 'ferroanalytics-tema'

type Tema = 'light' | 'dark'

function temaActual(): Tema {
  return document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light'
}

export function ModoTema({ compacto = false }: { compacto?: boolean }) {
  const [tema, setTema] = useState<Tema>(temaActual)
  const oscuro = tema === 'dark'

  function alternarTema() {
    const siguiente: Tema = oscuro ? 'light' : 'dark'
    document.documentElement.dataset.theme = siguiente
    localStorage.setItem(CLAVE_TEMA, siguiente)
    setTema(siguiente)
  }

  return (
    <button
      type="button"
      onClick={alternarTema}
      aria-label={oscuro ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'}
      title={oscuro ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'}
      className={`fa-theme-toggle ${compacto ? 'fa-theme-toggle--compact' : ''}`}
    >
      <span className="fa-theme-toggle__icon" aria-hidden="true">
        {oscuro ? <IconoSol /> : <IconoLuna />}
      </span>
      {!compacto && <span>{oscuro ? 'Modo claro' : 'Modo oscuro'}</span>}
    </button>
  )
}

function IconoSol() {
  return (
    <svg viewBox="0 0 20 20" width="17" height="17" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round">
      <circle cx="10" cy="10" r="3.2" />
      <path d="M10 2.2v1.6M10 16.2v1.6M2.2 10h1.6M16.2 10h1.6M4.5 4.5l1.1 1.1M14.4 14.4l1.1 1.1M15.5 4.5l-1.1 1.1M5.6 14.4l-1.1 1.1" />
    </svg>
  )
}

function IconoLuna() {
  return (
    <svg viewBox="0 0 20 20" width="17" height="17" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <path d="M16.4 12.8A6.8 6.8 0 0 1 7.2 3.6 6.8 6.8 0 1 0 16.4 12.8Z" />
    </svg>
  )
}
