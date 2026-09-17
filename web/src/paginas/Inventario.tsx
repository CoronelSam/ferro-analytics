import { useMemo, useState } from 'react'
import { Estado } from '../componentes/Estado'
import { Cabecera } from '../componentes/Cabecera'
import { CategoriaBadge } from '../componentes/CategoriaBadge'
import { BadgeEstado } from '../componentes/BadgeEstado'
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

  const bajos = (productos.data ?? []).filter((p) => p.stock_actual > 0 && p.stock_actual < p.stock_minimo).length
  const agotados = (productos.data ?? []).filter((p) => p.stock_actual === 0).length

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

      <div className="flex flex-col gap-5 px-8 py-7">
        <div className="grid grid-cols-3 gap-3">
          <ResumenMini etiqueta="Productos registrados" valor={(productos.data?.length ?? 0).toLocaleString('es-HN')} />
          <ResumenMini etiqueta="Stock bajo" valor={bajos.toLocaleString('es-HN')} tono="naranja" />
          <ResumenMini etiqueta="Agotados" valor={agotados.toLocaleString('es-HN')} tono="rojo" />
        </div>

        <div className="fa-toolbar flex flex-wrap items-center gap-2.5 p-3.5">
          <div className="flex min-w-[280px] flex-1 items-center gap-2 rounded-xl border border-[#DCE5EF] bg-[#F8FAFD] px-3 py-2.5">
            <IconoBuscar size={16} className="text-[#8A98AA]" />
            <input
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
              placeholder="Buscar por código o nombre..."
              className="w-full bg-transparent text-[13px] font-semibold text-[#243B55] placeholder:text-[#8A98AA] focus:outline-none"
            />
          </div>

          <div className="relative">
            <select
              value={idCategoria ?? ''}
              onChange={(e) => setIdCategoria(e.target.value ? Number(e.target.value) : null)}
              className="appearance-none rounded-xl border border-[#DCE5EF] bg-white py-2.5 pl-3.5 pr-9 text-[12.5px] font-bold text-[#43566F]"
            >
              <option value="">Todas las categorías</option>
              {categorias.data?.map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
            </select>
            <IconoChevronAbajo size={13} className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-[#6D7B8F]" />
          </div>

          <button
            onClick={() => setSoloStockBajo((v) => !v)}
            className={`rounded-xl border px-3.5 py-2.5 text-[12.5px] font-extrabold ${
              soloStockBajo
                ? 'border-[#124E96] bg-[#124E96] text-white shadow-[0_6px_16px_rgba(18,78,150,.16)]'
                : 'border-[#DCE5EF] bg-white text-[#43566F] hover:border-[#AFC3DA] hover:bg-[#F8FBFF]'
            }`}
          >
            Solo stock bajo
          </button>
        </div>

        <Estado cargando={productos.isLoading || categorias.isLoading} error={productos.error ?? categorias.error} vacio={filtrados.length === 0} mensajeVacio={productos.data?.length ? 'Ningún producto coincide con los filtros seleccionados.' : 'No hay productos importados todavía.'}>
          <div className="fa-table-wrap">
            <table className="w-full text-sm">
              <thead className="text-left text-[10.5px] font-extrabold uppercase tracking-[0.07em]">
                <tr>
                  <th className="px-4 py-3">Código</th>
                  <th className="px-4 py-3">Nombre</th>
                  <th className="px-4 py-3">Categoría</th>
                  <th className="px-4 py-3 text-right">Precio</th>
                  <th className="px-4 py-3 text-right">Stock</th>
                  <th className="px-4 py-3 text-right">Mínimo</th>
                  <th className="px-4 py-3">Estado</th>
                </tr>
              </thead>
              <tbody>
                {filtrados.map((p) => {
                  const agotado = p.stock_actual === 0
                  const bajo = !agotado && p.stock_actual < p.stock_minimo
                  const estado = agotado ? 'agotado' : bajo ? 'bajo' : 'normal'
                  return (
                    <tr key={p.codigo} className={agotado ? 'bg-red-50/35' : bajo ? 'bg-orange-50/30' : ''}>
                      <td className="px-4 py-3.5 font-mono text-xs font-extrabold text-[#53647A]">{p.codigo}</td>
                      <td className="px-4 py-3.5 text-[13px] font-extrabold text-[#13233A]">{p.nombre}</td>
                      <td className="px-4 py-3.5">
                        <CategoriaBadge idCategoria={p.id_categoria} nombre={categorias.data?.find((c) => c.id === p.id_categoria)?.nombre ?? `Categoría ${p.id_categoria}`} />
                      </td>
                      <td className="px-4 py-3.5 text-right text-[13px] font-semibold text-[#43566F]">{formatearLempiras(p.precio_unitario)}</td>
                      <td className="px-4 py-3.5 text-right text-[13px] font-extrabold text-[#13233A]">{p.stock_actual}</td>
                      <td className="px-4 py-3.5 text-right text-[13px] font-semibold text-[#6D7B8F]">{p.stock_minimo}</td>
                      <td className="px-4 py-3.5"><BadgeEstado estado={estado} /></td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
            <div className="flex items-center justify-between border-t border-[#E8EEF5] bg-[#FAFBFD] px-4 py-3 text-xs font-semibold text-[#6D7B8F]">
              <span>Mostrando {filtrados.length} de {productos.data?.length ?? 0} productos</span>
              {(busqueda || idCategoria !== null || soloStockBajo) && <span>Filtros activos</span>}
            </div>
          </div>
        </Estado>
      </div>
    </div>
  )
}

function ResumenMini({ etiqueta, valor, tono = 'azul' }: { etiqueta: string; valor: string; tono?: 'azul' | 'naranja' | 'rojo' }) {
  const estilos = tono === 'azul' ? 'bg-[#EAF2FC] text-[#124E96]' : tono === 'naranja' ? 'bg-[#FFF1E7] text-[#E65F00]' : 'bg-red-50 text-red-600'
  return (
    <div className="fa-card flex items-center justify-between px-4 py-3.5">
      <span className="text-[12px] font-bold text-[#6D7B8F]">{etiqueta}</span>
      <span className={`rounded-lg px-2.5 py-1 text-[13px] font-extrabold ${estilos}`}>{valor}</span>
    </div>
  )
}
