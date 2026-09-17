import { useMemo, useState } from 'react'
import { Estado } from '../componentes/Estado'
import { Cabecera } from '../componentes/Cabecera'
import { CategoriaBadge } from '../componentes/CategoriaBadge'
import { BotonFantasma, BotonPrimario } from '../componentes/Boton'
import { IconoBuscar, IconoChevronAbajo, IconoDescargar, IconoImportar } from '../componentes/Icono'
import { formatearLempiras } from '../lib/api'
import { useCategorias, useProductos } from '../lib/consultas'
import { descargarCSV } from '../lib/csv'

export function Inventario() {
  const productos = useProductos()
  const categorias = useCategorias()
  const [busqueda, setBusqueda] = useState('')
  const [idCategoria, setIdCategoria] = useState<number | null>(null)
  const [soloStockBajo, setSoloStockBajo] = useState(false)

  const filtrados = useMemo(() => {
    const q = busqueda.trim().toLowerCase()
    return (productos.data ?? []).filter((p) => {
      if (q && !p.codigo.toLowerCase().includes(q) && !p.nombre.toLowerCase().includes(q)) return false
      if (idCategoria !== null && p.id_categoria !== idCategoria) return false
      if (soloStockBajo && p.stock_actual >= p.stock_minimo) return false
      return true
    })
  }, [productos.data, busqueda, idCategoria, soloStockBajo])

  return (
    <div className="flex flex-col">
      <Cabecera titulo="Inventario" subtitulo={`${productos.data?.length ?? 0} productos activos en ${categorias.data?.length ?? 0} categorías.`}>
        <BotonFantasma onClick={() => descargarCSV('inventario', filtrados)} disabled={!filtrados.length}>
          <IconoDescargar size={16} />
          Exportar
        </BotonFantasma>
        <BotonPrimario>
          <IconoImportar size={16} />
          Importar productos
        </BotonPrimario>
      </Cabecera>

      <div className="flex flex-col gap-4 px-8 py-7">
        <div className="flex items-center gap-2.5">
          <div className="flex w-[240px] items-center gap-2 rounded-[9px] border border-neutral-200 bg-neutral-50 px-3 py-2">
            <IconoBuscar size={16} className="text-neutral-400" />
            <input
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
              placeholder="Buscar por código o nombre..."
              className="w-full bg-transparent text-[13px] font-semibold text-neutral-800 placeholder:text-neutral-400 focus:outline-none"
            />
          </div>

          <div className="relative">
            <select
              value={idCategoria ?? ''}
              onChange={(e) => setIdCategoria(e.target.value ? Number(e.target.value) : null)}
              className="appearance-none rounded-full border border-neutral-200 bg-white py-2 pl-3.5 pr-8 text-[12.5px] font-bold text-neutral-700"
            >
              <option value="">Todas las categorías</option>
              {categorias.data?.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.nombre}
                </option>
              ))}
            </select>
            <IconoChevronAbajo size={13} className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 text-neutral-500" />
          </div>

          <button
            onClick={() => setSoloStockBajo((v) => !v)}
            className={`rounded-full border px-3.5 py-2 text-[12.5px] font-bold ${
              soloStockBajo ? 'border-neutral-900 bg-neutral-900 text-white' : 'border-neutral-200 bg-white text-neutral-700'
            }`}
          >
            Solo stock bajo
          </button>
        </div>

        <Estado
          cargando={productos.isLoading || categorias.isLoading}
          error={productos.error ?? categorias.error}
          vacio={filtrados.length === 0}
          mensajeVacio={productos.data?.length ? 'Ningún producto coincide con el filtro.' : 'No hay productos importados todavía.'}
        >
          <div className="overflow-hidden rounded-[14px] border border-neutral-200 bg-white">
            <table className="w-full text-sm">
              <thead className="bg-neutral-50 text-left text-[10.5px] font-extrabold uppercase tracking-wide text-neutral-500">
                <tr>
                  <th className="px-4 py-2.5">Código</th>
                  <th className="px-4 py-2.5">Nombre</th>
                  <th className="px-4 py-2.5">Categoría</th>
                  <th className="px-4 py-2.5 text-right">Precio</th>
                  <th className="px-4 py-2.5 text-right">Stock</th>
                  <th className="px-4 py-2.5 text-right">Mínimo</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-100">
                {filtrados.map((p) => {
                  const bajo = p.stock_actual < p.stock_minimo
                  return (
                    <tr key={p.codigo} className={bajo ? 'bg-red-50' : undefined}>
                      <td className="px-4 py-3 font-mono text-xs font-bold text-neutral-700">{p.codigo}</td>
                      <td className="px-4 py-3 text-[13px] font-bold text-neutral-900">{p.nombre}</td>
                      <td className="px-4 py-3">
                        <CategoriaBadge idCategoria={p.id_categoria} nombre={categorias.data?.find((c) => c.id === p.id_categoria)?.nombre ?? `Categoría ${p.id_categoria}`} />
                      </td>
                      <td className="px-4 py-3 text-right text-[13px] font-semibold text-neutral-700">{formatearLempiras(p.precio_unitario)}</td>
                      <td className="px-4 py-3 text-right">
                        <span className="inline-flex items-center gap-1.5 text-[13px] font-extrabold text-neutral-900">
                          <span className={`h-1.5 w-1.5 rounded-full ${bajo ? 'bg-red-600' : 'bg-emerald-700'}`} />
                          {p.stock_actual}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right text-[13px] font-semibold text-neutral-500">{p.stock_minimo}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
            <div className="px-4 py-3 text-xs font-semibold text-neutral-500">
              Mostrando {filtrados.length} de {productos.data?.length ?? 0} productos
            </div>
          </div>
        </Estado>
      </div>
    </div>
  )
}
