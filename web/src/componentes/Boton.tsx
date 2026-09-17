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
      className="flex items-center gap-1.5 whitespace-nowrap rounded-[10px] bg-[#FF7A1A] px-4 py-2.5 text-[13.5px] font-extrabold text-white shadow-[0_6px_14px_rgba(255,122,26,0.22)] hover:bg-[#E65F00] hover:-translate-y-px disabled:translate-y-0 disabled:opacity-40"
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
      className="flex items-center gap-1.5 whitespace-nowrap rounded-[10px] border border-[#CBD8E7] bg-white px-4 py-2.5 text-[13.5px] font-bold text-[#124E96] hover:border-[#9AB7D8] hover:bg-[#EAF2FC] disabled:opacity-40"
    >
      {children}
    </button>
  )
}
