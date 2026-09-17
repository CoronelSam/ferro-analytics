"""
Interfaz de consola para FerroAnalytics (Fase I).
Coordina entrada/salida del usuario; la lógica de negocio vive en los
módulos importador, almacenamiento y reportes.
"""

import csv
import os
from datetime import datetime

import src.almacenamiento as alm
import src.clasificacion as clf
import src.importador as imp
import src.importador_bd as imp_bd
import src.prediccion as pred
import src.reportes as rep
from src.excepciones import ErrorAlmacenamiento, ErrorImportacion, FerroAnalyticsError

DIRECTORIO_REPORTES = os.path.join("data", "reportes")

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


def _ofrecer_exportar(datos: list, nombre_sugerido: str) -> None:
    """
    Pregunta al usuario si desea exportar los datos a CSV.
    Escribe el archivo en data/reportes/ usando csv.writer.

    Recibe:
        datos           : lista de dicts (salida de cualquier función de reportes).
        nombre_sugerido : nombre de archivo por defecto (sin extensión).
    """
    if not datos:
        return
    respuesta = input("\n  ¿Exportar a CSV? [s/N]: ").strip().lower()
    if respuesta != "s":
        return

    nombre_default = f"{nombre_sugerido}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    entrada = input(f"  Nombre del archivo [{nombre_default}]: ").strip()
    nombre_archivo = entrada if entrada else nombre_default

    os.makedirs(DIRECTORIO_REPORTES, exist_ok=True)
    ruta = os.path.join(DIRECTORIO_REPORTES, nombre_archivo)

    with open(ruta, "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=datos[0].keys())
        escritor.writeheader()
        escritor.writerows(datos)

    print(f"  Exportado: {ruta}")


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
    except ErrorImportacion as e:
        print(f"\n  Error al importar el archivo: {e}")
    except ErrorAlmacenamiento as e:
        print(f"\n  Error al guardar los datos: {e}")

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
        print(f"\n  Lote: {aceptados[0].lote_origen}  (para deshacer esta importación, opción 9)")
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

    visibles = []
    for p in sorted(productos, key=lambda x: x.codigo):
        if filtro and filtro not in p.codigo.lower() and filtro not in p.nombre.lower():
            continue
        cat = nombres_cat.get(p.id_categoria, f"Cat.{p.id_categoria}")
        alerta = " !" if p.stock_actual < p.stock_minimo else ""
        print(f"  {p.codigo:<10} {p.nombre:<25} {cat:<15} "
              f"{p.precio_unitario:>8.2f} {p.stock_actual:>6}{alerta:>3} {p.stock_minimo:>4}")
        visibles.append(p)

    _linea()
    if visibles:
        precio_promedio = sum(p.precio_unitario for p in visibles) / len(visibles)
        stock_total     = sum(p.stock_actual for p in visibles)
        valor_total     = sum(p.stock_actual * p.precio_unitario for p in visibles)
        print(f"  {len(visibles)} producto(s)  |  "
              f"Precio prom.: L{precio_promedio:.2f}  |  "
              f"Stock total: {stock_total}  |  "
              f"Valor total: L{valor_total:,.2f}")
    else:
        print("  Sin resultados para el filtro aplicado.")
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
    print(f"\n  {'CATEGORÍA':<20} {'PRODUCTOS':>9} {'STOCK':>8} {'VALOR (L)':>12}")
    _linea()
    for r in datos:
        print(f"  {r['nombre']:<20} {r['num_productos']:>9} "
              f"{r['stock_total']:>8} {r['valor_total']:>12.2f}")
    _linea()
    total_stock = sum(r["stock_total"] for r in datos)
    total_valor = sum(r["valor_total"] for r in datos)
    print(f"  {'TOTAL':<20} {len(productos):>9} {total_stock:>8} {total_valor:>12.2f}")
    _ofrecer_exportar(datos, "stock_por_categoria")
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

    print(f"\n  {'#':<3} {'CÓDIGO':<10} {'NOMBRE':<25} {'STOCK':>6} {'VALOR (L)':>10} {'ÚLT. SALIDA':<12}")
    _linea()
    for i, r in enumerate(datos, 1):
        salida = r["ultima_salida"] or "Sin salidas"
        print(f"  {i:<3} {r['codigo']:<10} {r['nombre']:<25} "
              f"{r['stock_actual']:>6} {r['valor_inmovilizado']:>10.2f} {salida:<12}")
    _ofrecer_exportar(datos, "top_inmovilizado")
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
    _ofrecer_exportar(datos, "ventas_mensuales")
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
    _ofrecer_exportar(alertas, "alertas_stock_bajo")
    _pausar()


# ──────────────────────────────────────────────
# Opción 6: Clasificación ABC-XYZ
# ──────────────────────────────────────────────

# Etiquetas en lenguaje llano para las clases técnicas ABC/XYZ.
_ETIQUETA_ABC = {"A": "Alta", "B": "Media", "C": "Baja"}
_ETIQUETA_XYZ = {"X": "Estable", "Y": "Variable", "Z": "Irregular"}


def _ver_clasificacion_abc_xyz() -> None:
    _titulo("CLASIFICACIÓN ABC-XYZ")

    productos = alm.leer_productos()
    movimientos = alm.leer_movimientos()
    if not productos:
        print("  No hay productos almacenados.")
        _pausar()
        return

    print("  Prioridad (A/B/C): qué tanto pesa el producto en las ventas.")
    print("  Demanda (X/Y/Z): qué tan estable es su demanda mes a mes.")

    clasificacion = clf.clasificar_abc_xyz(productos, movimientos)
    resumen = clf.resumen_matriz(clasificacion)

    for r in resumen:
        prioridad = _ETIQUETA_ABC[r["clase_abc"]]
        demanda = _ETIQUETA_XYZ[r["clase_xyz"]]
        print(f"\n  [{r['celda']}] Prioridad {prioridad} · Demanda {demanda}  "
              f"({r['num_productos']} productos, L {r['valor_consumo_total']:,.2f})")
        print(f"        {r['recomendacion']}")

    _seccion("Detalle por producto")
    print(f"  {'CÓDIGO':<10} {'NOMBRE':<25} {'VALOR (L)':>12} {'CV':>7}  {'PRIORIDAD':<10} {'DEMANDA':<12}")
    _linea()
    for r in clasificacion:
        cv_txt = f"{r['cv_demanda']:.2f}" if r["cv_demanda"] is not None else "—"
        prioridad = f"{_ETIQUETA_ABC[r['clase_abc']]} ({r['clase_abc']})"
        demanda = f"{_ETIQUETA_XYZ[r['clase_xyz']]} ({r['clase_xyz']})"
        print(f"  {r['codigo']:<10} {r['nombre']:<25} {r['valor_consumo']:>12,.2f} {cv_txt:>7}  {prioridad:<10} {demanda:<12}")

    _ofrecer_exportar(clasificacion, "clasificacion_abc_xyz")
    _pausar()


# ──────────────────────────────────────────────
# Opción 7: Predicción de demanda
# ──────────────────────────────────────────────

def _ver_prediccion_demanda() -> None:
    _titulo("PREDICCIÓN DE DEMANDA")

    productos = alm.leer_productos()
    movimientos = alm.leer_movimientos()
    categorias = alm.leer_categorias()
    if not movimientos:
        print("  No hay movimientos almacenados.")
        _pausar()
        return

    print("  [1] Por categoría")
    print("  [2] Por producto (clase A/X: alto valor y demanda estable)")
    modo = _pedir_opcion({"1", "2"})
    n = _pedir_entero("  Meses a pronosticar (por defecto 3)", minimo=1)

    if modo == "1":
        print("\n  Categorías disponibles:")
        for c in categorias:
            print(f"    [{c.id}] {c.nombre}")
        id_categoria = int(_pedir_opcion({str(c.id) for c in categorias}, "  Id de categoría"))
        resultado = pred.pronosticar_categoria(productos, movimientos, categorias, id_categoria, n=n)
        _mostrar_pronostico(resultado)
    else:
        prioritarios = pred.productos_prioritarios(productos, movimientos)
        if not prioritarios:
            print("\n  Ningún producto quedó clasificado como A/X todavía.")
            _pausar()
            return
        print(f"\n  Productos A/X disponibles: {', '.join(prioritarios)}")
        codigo = _pedir_opcion(set(prioritarios), "  Código de producto")
        tiempo_entrega = _pedir_entero("  Tiempo de entrega del proveedor en días (por defecto 7)", minimo=1)
        resultado = pred.pronosticar_producto(productos, movimientos, codigo, n=n, tiempo_entrega_dias=tiempo_entrega)
        _mostrar_pronostico(resultado)
        print(f"\n  Punto de reorden        : {resultado['punto_reorden']:.2f} uds")
        print(f"  Stock de seguridad      : {resultado['stock_seguridad']:.2f} uds")
        print(f"  Demanda diaria media    : {resultado['demanda_diaria_media']:.2f} uds")

    _pausar()


def _mostrar_pronostico(resultado: dict) -> None:
    print("\n  Comparación de modelos (backtest, menor MAE es mejor):")
    _linea()
    for m in resultado["comparacion_modelos"]:
        marca = "  <- mejor" if m["modelo"] == resultado["mejor_modelo"] else ""
        mape_txt = f"{m['mape']:.2f}%" if m["mape"] is not None else "—"
        print(f"    {m['modelo']:<22} MAE: {m['mae']:>9.3f}   MAPE: {mape_txt:>8}{marca}")

    print(f"\n  Pronóstico ({resultado['mejor_modelo']}):")
    for (anio, mes), valor in zip(resultado["meses_pronosticados"], resultado["pronostico"]):
        print(f"    {anio}-{mes:02d}: {valor:>10.2f} uds")


# ──────────────────────────────────────────────
# Opción 9: Importar desde base de datos (Postgres o MySQL)
# ──────────────────────────────────────────────

def _importar_desde_bd() -> None:
    _titulo("IMPORTAR DESDE BASE DE DATOS (POSTGRES O MYSQL)")
    print("  Requiere la variable de entorno FERRO_BD_URL, p. ej.:")
    print("    postgresql+psycopg://usuario:clave@host:5432/basededatos")
    print("    mysql+pymysql://usuario:clave@host:3306/basededatos")

    try:
        engine = imp_bd.crear_engine()
    except ErrorImportacion as e:
        print(f"\n  Error: {e}")
        _pausar()
        return

    print(f"\n  Conexión establecida ({imp_bd.nombre_motor(engine)}).")
    print("  Tipo de datos:")
    print("  [1] Categorías")
    print("  [2] Productos")
    print("  [3] Movimientos")
    tipo = _pedir_opcion({"1", "2", "3"})

    try:
        if tipo == "1":
            aceptadas, rechazadas = imp_bd.importar_categorias_desde_bd(engine)
            if aceptadas:
                alm.guardar_categorias(aceptadas)
            _mostrar_resultado_importacion("categorías", len(aceptadas), rechazadas)
        elif tipo == "2":
            aceptados, rechazados = imp_bd.importar_productos_desde_bd(engine)
            if aceptados:
                resultado = alm.guardar_productos(aceptados)
                print(f"\n  Insertados: {resultado['insertados']}  |  "
                      f"Actualizados: {resultado['actualizados']}")
            _mostrar_resultado_importacion("productos", len(aceptados), rechazados)
        else:
            codigos = alm.obtener_codigos_productos()
            ids_existentes = alm.obtener_ids_movimientos()
            desde_id = max(ids_existentes) if ids_existentes else None
            aceptados, rechazados = imp_bd.importar_movimientos_desde_bd(
                engine, codigos, ids_existentes, desde_id=desde_id)
            if aceptados:
                alm.guardar_movimientos(aceptados)
                print(f"\n  Lote: {aceptados[0].lote_origen}  (para deshacer esta sincronización, opción 9)")
            _mostrar_resultado_importacion("movimientos", len(aceptados), rechazados)
    except ErrorImportacion as e:
        print(f"\n  Error al importar: {e}")
    except ErrorAlmacenamiento as e:
        print(f"\n  Error al guardar los datos: {e}")

    _pausar()


# ──────────────────────────────────────────────
# Opción 10: Deshacer una importación de movimientos
# ──────────────────────────────────────────────

def _deshacer_lote_movimientos() -> None:
    _titulo("DESHACER UNA IMPORTACIÓN DE MOVIMIENTOS")

    lotes = alm.listar_lotes_movimientos()
    if not lotes:
        print("  No hay ninguna importación de movimientos identificada por lote.")
        print("  (Los movimientos importados antes de esta función no tienen lote asignado.)")
        _pausar()
        return

    print(f"\n  {'#':<3} {'LOTE':<28} {'CANTIDAD':>9} {'DESDE':<12} {'HASTA':<12}")
    _linea()
    for i, l in enumerate(lotes, 1):
        print(f"  {i:<3} {l['lote']:<28} {l['cantidad']:>9} {l['fecha_desde']:<12} {l['fecha_hasta']:<12}")

    print("\n  [0] Cancelar")
    opciones_validas = {"0"} | {str(i) for i in range(1, len(lotes) + 1)}
    opcion = _pedir_opcion(opciones_validas, "  Elija el lote a deshacer")
    if opcion == "0":
        print("  Cancelado.")
        _pausar()
        return

    lote = lotes[int(opcion) - 1]
    print(f"\n  Va a eliminar {lote['cantidad']} movimiento(s) del lote '{lote['lote']}'.")
    confirmacion = input("  Esta acción no se puede deshacer. ¿Continuar? [s/N]: ").strip().lower()
    if confirmacion != "s":
        print("  Cancelado.")
        _pausar()
        return

    eliminados = alm.eliminar_movimientos_por_lote(lote["lote"])
    print(f"\n  Eliminados: {eliminados} movimiento(s).")
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
        print("  [6] Clasificación ABC-XYZ")
        print("  [7] Predicción de demanda")
        print("  [8] Importar desde base de datos (Postgres/MySQL)")
        print("  [9] Deshacer una importación de movimientos")
        print("  [10] Salir")
        opcion = _pedir_opcion({"1", "2", "3", "4", "5", "6", "7", "8", "9", "10"})

        try:
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
                _ver_clasificacion_abc_xyz()
            elif opcion == "7":
                _ver_prediccion_demanda()
            elif opcion == "8":
                _importar_desde_bd()
            elif opcion == "9":
                _deshacer_lote_movimientos()
            elif opcion == "10":
                print("\n  Hasta luego.\n")
                break
        except FerroAnalyticsError as e:
            print(f"\n  Error: {e}")
            _pausar()
