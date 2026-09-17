// Exportación de datos a CSV en el navegador, equivalente a
// menu._ofrecer_exportar() (consola): mismo nombre de archivo sugerido
// (sufijo AAAAMMDD_HHMMSS) y mismas columnas que el dict de origen.

function formatearMarcaDeTiempo(fecha: Date): string {
  const p = (n: number) => String(n).padStart(2, '0')
  return (
    `${fecha.getFullYear()}${p(fecha.getMonth() + 1)}${p(fecha.getDate())}_` +
    `${p(fecha.getHours())}${p(fecha.getMinutes())}${p(fecha.getSeconds())}`
  )
}

function escaparCampo(valor: unknown): string {
  // precio_unitario y similares vienen de un float32 (struct 'f' en
  // almacenamiento.py), que al leerse como float64 de JS arrastra ruido de
  // precisión (0.07999999821186066 en vez de 0.08); redondear a 2
  // decimales lo evita sin afectar enteros (stock, ids, años).
  const numero = typeof valor === 'number' && !Number.isInteger(valor) ? Math.round(valor * 100) / 100 : valor
  const texto = numero === null || numero === undefined ? '' : String(numero)
  return /[",\r\n]/.test(texto) ? `"${texto.replace(/"/g, '""')}"` : texto
}

/**
 * Descarga `filas` como CSV. No hace nada si `filas` está vacío, igual que
 * `_ofrecer_exportar` en el menú de consola.
 */
export function descargarCSV<T extends object>(nombreSugerido: string, filas: readonly T[]): void {
  if (filas.length === 0) return

  const columnas = Object.keys(filas[0]) as (keyof T)[]
  const lineas = [
    columnas.join(','),
    ...filas.map((fila) => columnas.map((c) => escaparCampo(fila[c])).join(',')),
  ]

  const blob = new Blob([lineas.join('\r\n')], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const enlace = document.createElement('a')
  enlace.href = url
  enlace.download = `${nombreSugerido}_${formatearMarcaDeTiempo(new Date())}.csv`
  enlace.click()
  URL.revokeObjectURL(url)
}
