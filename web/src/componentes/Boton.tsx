import type { ReactNode } from 'react'

type Props = {
  children: ReactNode
  onClick?: () => void
  type?: 'button' | 'submit'
  disabled?: boolean
}

export function BotonPrimario({ children, onClick, type = 'button', disabled }: Props) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className="flex items-center gap-1.5 whitespace-nowrap rounded-[9px] bg-neutral-900 px-4 py-2.5 text-[13.5px] font-bold text-white disabled:opacity-40"
    >
      {children}
    </button>
  )
}

export function BotonFantasma({ children, onClick, type = 'button', disabled }: Props) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className="flex items-center gap-1.5 whitespace-nowrap rounded-[9px] border border-neutral-200 bg-white px-4 py-2.5 text-[13.5px] font-bold text-neutral-700 disabled:opacity-40"
    >
      {children}
    </button>
  )
}
