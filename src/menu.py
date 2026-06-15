"""
Interfaz de consola para FerroAnalytics (Fase I).
Coordina entrada/salida del usuario; la lógica de negocio vive en los
módulos importador, almacenamiento y reportes.
"""

import os
from datetime import datetime

import src.almacenamiento as alm
import src.importador as imp
import src.reportes as rep

# ──────────────────────────────────────────────
# Utilidades de presentación
# ──────────────────────────────────────────────

_ANCHO = 60


def _linea(caracter: str = "─") -> None:
    print(caracter * _ANCHO)


def _titulo(texto: str) -> None:
    _linea("═")
    print(f"  {texto}")
    _linea("═")


def _seccion(texto: str) -> None:
    print()
    _linea()
    print(f"  {texto}")
    _linea()


def _pausar() -> None:
    input("\nPresione Enter para continuar...")


def _pedir_opcion(opciones: set, mensaje: str = "Opción") -> str:
    """Repite el prompt hasta obtener una opción válida."""
    while True:
        valor = input(f"{mensaje}: ").strip()
        if valor in opciones:
            return valor
        print(f"  Opción no válida. Elija entre: {', '.join(sorted(opciones))}")


def _pedir_entero(mensaje: str, minimo: int = 1) -> int:
    """Repite el prompt hasta obtener un entero >= minimo."""
    while True:
        try:
            valor = int(input(f"{mensaje}: ").strip())
            if valor >= minimo:
                return valor
            print(f"  Debe ser un número mayor o igual a {minimo}.")
        except ValueError:
            print("  Ingrese un número entero válido.")


def _pedir_fecha(mensaje: str) -> str:
    """Repite el prompt hasta obtener una cadena con formato AAAA-MM-DD válido."""
    while True:
        valor = input(f"{mensaje} (AAAA-MM-DD): ").strip()
        try:
            datetime.strptime(valor, "%Y-%m-%d")
            return valor
        except ValueError:
            print("  Formato inválido. Use AAAA-MM-DD (p. ej. 2026-01-15).")


# ──────────────────────────────────────────────
# Opción 1: Importar datos
# ──────────────────────────────────────────────

def _importar_csv() -> None:
    _titulo("IMPORTAR DATOS (CSV)")
    print("  Tipo de archivo:")
    print("  [1] categorias.csv")
    print("  [2] productos.csv")
    print("  [3] movimientos.csv")
    tipo = _pedir_opcion({"1", "2", "3"})

    ruta = input("  Ruta del archivo: ").strip()
    if not os.path.isfile(ruta):
        print(f"\n  Error: no se encontró el archivo '{ruta}'.")
        _pausar()
        return

    nombre_archivo = os.path.basename(ruta)

    if alm.archivo_ya_importado(nombre_archivo):
        print(f"\n  Aviso: '{nombre_archivo}' ya fue importado anteriormente.")
        confirmacion = input("  ¿Importar igualmente? [s/N]: ").strip().lower()
        if confirmacion != "s":
            print("  Importación cancelada.")
            _pausar()
            return

    try:
        if tipo == "1":
            _importar_categorias(ruta, nombre_archivo)
        elif tipo == "2":
            _importar_productos(ruta, nombre_archivo)
        else:
            _importar_movimientos(ruta, nombre_archivo)
    except (ValueError, OSError) as e:
        print(f"\n  Error al leer el archivo: {e}")

    _pausar()


def _importar_categorias(ruta: str, nombre_archivo: str) -> None:
    aceptadas, rechazadas = imp.importar_categorias(ruta)
    if aceptadas:
        alm.guardar_categorias(aceptadas)
        alm.registrar_importacion(nombre_archivo)
    _mostrar_resultado_importacion("categorías", len(aceptadas), rechazadas)


def _importar_productos(ruta: str, nombre_archivo: str) -> None:
    aceptados, rechazados = imp.importar_productos(ruta)
    if aceptados:
        resultado = alm.guardar_productos(aceptados)
        alm.registrar_importacion(nombre_archivo)
        print(f"\n  Insertados: {resultado['insertados']}  |  "
              f"Actualizados: {resultado['actualizados']}")
    _mostrar_resultado_importacion("productos", len(aceptados), rechazados)


def _importar_movimientos(ruta: str, nombre_archivo: str) -> None:
    codigos = alm.obtener_codigos_productos()
    ids_existentes = alm.obtener_ids_movimientos()
    aceptados, rechazados = imp.importar_movimientos(ruta, codigos, ids_existentes)
    if aceptados:
        alm.guardar_movimientos(aceptados)
        alm.registrar_importacion(nombre_archivo)
    _mostrar_resultado_importacion("movimientos", len(aceptados), rechazados)


def _mostrar_resultado_importacion(entidad: str, n_ok: int, rechazadas: list) -> None:
    print(f"\n  Aceptados : {n_ok}")
    print(f"  Rechazados: {len(rechazadas)}")
    if rechazadas:
        print(f"\n  Filas rechazadas:")
        for r in rechazadas:
            print(f"    Fila {r['fila']:>3}: {r['motivo']}")


# ──────────────────────────────────────────────
# Opción 2: Consultar inventario actual
# ──────────────────────────────────────────────

def _consultar_inventario() -> None:
    _titulo("INVENTARIO ACTUAL")

    productos = alm.leer_productos()
    if not productos:
        print("  No hay productos almacenados.")
        _pausar()
        return

    categorias = alm.leer_categorias()
    nombres_cat = {c.id: c.nombre for c in categorias}

    print(f"\n  {'CÓDIGO':<10} {'NOMBRE':<25} {'CATEGORÍA':<15} "
          f"{'PRECIO':>8} {'STOCK':>6} {'MÍN':>5}")
    _linea()

    filtro = input("  Filtrar por código/nombre (Enter para ver todos): ").strip().lower()

    encontrados = 0
    for p in sorted(productos, key=lambda x: x.codigo):
        if filtro and filtro not in p.codigo.lower() and filtro not in p.nombre.lower():
            continue
        cat = nombres_cat.get(p.id_categoria, f"Cat.{p.id_categoria}")
        alerta = " !" if p.stock_actual < p.stock_minimo else ""
        print(f"  {p.codigo:<10} {p.nombre:<25} {cat:<15} "
              f"{p.precio_unitario:>8.2f} {p.stock_actual:>6}{alerta:>3} {p.stock_minimo:>4}")
        encontrados += 1

    _linea()
    print(f"  Total: {encontrados} producto(s)")
    _pausar()


# ──────────────────────────────────────────────
# Opción 3: Consultar movimientos por período
# ──────────────────────────────────────────────

def _consultar_movimientos() -> None:
    _titulo("MOVIMIENTOS POR PERÍODO")

    movimientos = alm.leer_movimientos()
    if not movimientos:
        print("  No hay movimientos almacenados.")
        _pausar()
        return

    fecha_desde = _pedir_fecha("  Desde")
    fecha_hasta = _pedir_fecha("  Hasta")

    if fecha_desde > fecha_hasta:
        print("  Error: la fecha inicial no puede ser posterior a la final.")
        _pausar()
        return

    print("  Tipo de movimiento:")
    print("  [E] Solo entradas")
    print("  [S] Solo salidas")
    print("  [T] Todos")
    tipo_filtro = _pedir_opcion({"E", "S", "T"}, "  Tipo").upper()

    filtrados = [
        m for m in movimientos
        if fecha_desde <= m.fecha <= fecha_hasta
        and (tipo_filtro == "T" or m.tipo == tipo_filtro)
    ]

    tipo_desc = {"E": "entradas", "S": "salidas", "T": "todos"}[tipo_filtro]
    if not filtrados:
        print(f"\n  Sin movimientos ({tipo_desc}) entre {fecha_desde} y {fecha_hasta}.")
        _pausar()
        return

    print(f"\n  {'ID':>6} {'PRODUCTO':<10} {'TIPO':<8} {'CANT':>6} {'FECHA':<12}")
    _linea()
    for m in sorted(filtrados, key=lambda x: (x.fecha, x.id_movimiento)):
        tipo_txt = "Entrada" if m.tipo == "E" else "Salida "
        print(f"  {m.id_movimiento:>6} {m.codigo_producto:<10} {tipo_txt:<8} "
              f"{m.cantidad:>6} {m.fecha:<12}")
    _linea()

    entradas = sum(m.cantidad for m in filtrados if m.tipo == "E")
    salidas  = sum(m.cantidad for m in filtrados if m.tipo == "S")
    print(f"  {len(filtrados)} movimiento(s)  |  Entradas: {entradas} uds  |  Salidas: {salidas} uds")
    _pausar()


# ──────────────────────────────────────────────
# Opción 4: Ver reportes
# ──────────────────────────────────────────────

def _ver_reportes() -> None:
    while True:
        _titulo("REPORTES")
        print("  [1] Stock total por categoría")
        print("  [2] Top productos con stock inmovilizado")
        print("  [3] Ventas mensuales por categoría")
        print("  [0] Volver")
        opcion = _pedir_opcion({"1", "2", "3", "0"})
        if opcion == "0":
            break
        productos  = alm.leer_productos()
        categorias = alm.leer_categorias()
        if opcion == "1":
            _reporte_stock_categoria(productos, categorias)
        elif opcion == "2":
            movimientos = alm.leer_movimientos()
            _reporte_top_inmovilizado(productos, movimientos)
        elif opcion == "3":
            movimientos = alm.leer_movimientos()
            _reporte_ventas_mensuales(movimientos, productos, categorias)


def _reporte_stock_categoria(productos: list, categorias: list) -> None:
    _seccion("Stock total por categoría")
    if not productos:
        print("  Sin datos.")
        _pausar()
        return

    datos = rep.stock_por_categoria(productos, categorias)
    print(f"\n  {'CATEGORÍA':<20} {'PRODUCTOS':>9} {'STOCK':>8} {'VALOR ($)':>12}")
    _linea()
    for r in datos:
        print(f"  {r['nombre']:<20} {r['num_productos']:>9} "
              f"{r['stock_total']:>8} {r['valor_total']:>12.2f}")
    _linea()
    total_stock = sum(r["stock_total"] for r in datos)
    total_valor = sum(r["valor_total"] for r in datos)
    print(f"  {'TOTAL':<20} {len(productos):>9} {total_stock:>8} {total_valor:>12.2f}")
    _pausar()


def _reporte_top_inmovilizado(productos: list, movimientos: list) -> None:
    _seccion("Top productos con stock inmovilizado")
    if not productos:
        print("  Sin datos.")
        _pausar()
        return

    n    = _pedir_entero("  Cantidad a mostrar (por defecto 10)", minimo=1)
    dias = _pedir_entero("  Días sin salida para considerar inmovilizado (por defecto 90)", minimo=1)

    datos = rep.top_inmovilizado(productos, movimientos, n=n, dias=dias)
    if not datos:
        print(f"\n  Ningún producto inmovilizado en los últimos {dias} días.")
        _pausar()
        return

    print(f"\n  {'#':<3} {'CÓDIGO':<10} {'NOMBRE':<25} {'STOCK':>6} {'VALOR ($)':>10} {'ÚLT. SALIDA':<12}")
    _linea()
    for i, r in enumerate(datos, 1):
        salida = r["ultima_salida"] or "Sin salidas"
        print(f"  {i:<3} {r['codigo']:<10} {r['nombre']:<25} "
              f"{r['stock_actual']:>6} {r['valor_inmovilizado']:>10.2f} {salida:<12}")
    _pausar()


def _reporte_ventas_mensuales(movimientos: list, productos: list, categorias: list) -> None:
    _seccion("Ventas mensuales por categoría")
    if not movimientos:
        print("  Sin datos.")
        _pausar()
        return

    datos = rep.ventas_mensuales_por_categoria(movimientos, productos, categorias)
    if not datos:
        print("  No hay movimientos de salida registrados.")
        _pausar()
        return

    mes_actual = None
    print()
    for r in datos:
        encabezado = f"{r['anio']}-{r['mes']:02d}"
        if encabezado != mes_actual:
            if mes_actual is not None:
                print()
            print(f"  {encabezado}")
            _linea("·")
            mes_actual = encabezado
        print(f"    {r['nombre_categoria']:<20} {r['unidades']:>6} uds")
    _pausar()


# ──────────────────────────────────────────────
# Opción 5: Alertas de stock bajo
# ──────────────────────────────────────────────

def _ver_alertas() -> None:
    _titulo("ALERTAS DE STOCK BAJO")

    productos = alm.leer_productos()
    if not productos:
        print("  No hay productos almacenados.")
        _pausar()
        return

    print("  [1] Usar mínimo de cada producto")
    print("  [2] Ingresar umbral global")
    modo = _pedir_opcion({"1", "2"})

    umbral = None
    if modo == "2":
        umbral = _pedir_entero("  Umbral mínimo de stock", minimo=0)

    categorias  = alm.leer_categorias()
    nombres_cat = {c.id: c.nombre for c in categorias}
    alertas     = rep.alertas_stock_bajo(productos, umbral)

    if not alertas:
        print("\n  Todos los productos tienen stock suficiente.")
        _pausar()
        return

    print(f"\n  {'CÓDIGO':<10} {'NOMBRE':<25} {'CATEGORÍA':<15} "
          f"{'ACTUAL':>7} {'MÍNIMO':>7} {'DEFICIT':>7}")
    _linea()
    for a in alertas:
        cat = nombres_cat.get(a["id_categoria"], f"Cat.{a['id_categoria']}")
        print(f"  {a['codigo']:<10} {a['nombre']:<25} {cat:<15} "
              f"{a['stock_actual']:>7} {a['minimo']:>7} {a['diferencia']:>7}")
    _linea()
    print(f"  {len(alertas)} producto(s) con stock bajo.")
    _pausar()


# ──────────────────────────────────────────────
# Bucle principal
# ──────────────────────────────────────────────

def ejecutar() -> None:
    """Inicia el bucle principal del menú de FerroAnalytics."""
    while True:
        _titulo("FerroAnalytics – Menú Principal")
        print("  [1] Importar datos (CSV)")
        print("  [2] Consultar inventario actual")
        print("  [3] Consultar movimientos por período")
        print("  [4] Ver reportes")
        print("  [5] Ver alertas de stock bajo")
        print("  [6] Salir")
        opcion = _pedir_opcion({"1", "2", "3", "4", "5", "6"})

        if opcion == "1":
            _importar_csv()
        elif opcion == "2":
            _consultar_inventario()
        elif opcion == "3":
            _consultar_movimientos()
        elif opcion == "4":
            _ver_reportes()
        elif opcion == "5":
            _ver_alertas()
        elif opcion == "6":
            print("\n  Hasta luego.\n")
            break
