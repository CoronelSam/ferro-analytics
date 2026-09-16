"""
Clasificación ABC-XYZ de productos para FerroAnalytics (Fase II).

ABC clasifica por valor de consumo (unidades vendidas × precio unitario
actual): A concentra el 80% del valor acumulado, B el siguiente 15% y C
el 5% restante. XYZ clasifica por la regularidad de la demanda mensual,
con el coeficiente de variación (desviación estándar / media): X es
regular (CV < 0.5), Y es variable (0.5 ≤ CV ≤ 1) y Z es irregular (CV > 1).

Como en el resto de la Fase II, la fecha de referencia es la del último
movimiento registrado, no date.today(): los históricos que se analizan no
necesariamente llegan hasta hoy.
"""

import statistics
from datetime import date, datetime

from src.excepciones import DatosInsuficientes

LIMITE_A = 0.80
LIMITE_B = 0.95

CV_LIMITE_X = 0.5
CV_LIMITE_Y = 1.0

# (clase_abc, clase_xyz) -> recomendación de manejo de inventario.
MATRIZ_RECOMENDACIONES = {
    ("A", "X"): "Alta prioridad, demanda estable: reposición automática y frecuente, stock de seguridad bajo.",
    ("A", "Y"): "Alta prioridad, demanda variable: monitoreo cercano, stock de seguridad moderado.",
    ("A", "Z"): "Alta prioridad, demanda irregular: revisión manual frecuente, evitar tanto quiebres como sobre-stock.",
    ("B", "X"): "Prioridad media, demanda estable: reposición periódica estándar.",
    ("B", "Y"): "Prioridad media, demanda variable: ajustar el stock de seguridad según temporada.",
    ("B", "Z"): "Prioridad media, demanda irregular: pedidos bajo demanda, vigilar que no se inmovilice.",
    ("C", "X"): "Baja prioridad, demanda estable: pedidos grandes y espaciados, control mínimo.",
    ("C", "Y"): "Baja prioridad, demanda variable: revisión ocasional, mantener stock mínimo.",
    ("C", "Z"): "Baja prioridad, demanda irregular: evaluar descontinuar o vender solo bajo pedido.",
}


# ──────────────────────────────────────────────
# Fecha de referencia y período de análisis
# ──────────────────────────────────────────────

def fecha_referencia(movimientos: list) -> date | None:
    """
    Fecha del último movimiento registrado, usada como "hoy" para todos los
    análisis de la Fase II en vez de date.today().

    Recibe:
        movimientos: lista de MovimientoAnalitico.

    Devuelve la fecha máxima (date), o None si la lista está vacía.
    """
    fechas = [datetime.strptime(m.fecha, "%Y-%m-%d").date() for m in movimientos]
    return max(fechas) if fechas else None


def meses_periodo(movimientos: list) -> list:
    """
    Lista ordenada de todos los pares (año, mes) entre el primer y el
    último movimiento registrado, sin huecos.
    """
    fechas = [datetime.strptime(m.fecha, "%Y-%m-%d").date() for m in movimientos]
    if not fechas:
        return []
    inicio, fin = min(fechas), max(fechas)
    meses = []
    anio, mes = inicio.year, inicio.month
    while (anio, mes) <= (fin.year, fin.month):
        meses.append((anio, mes))
        mes += 1
        if mes > 12:
            mes = 1
            anio += 1
    return meses


# ──────────────────────────────────────────────
# ABC por valor de consumo
# ──────────────────────────────────────────────

def valor_consumo_por_producto(productos: list, movimientos: list) -> dict:
    """
    Calcula el valor de consumo de cada producto: unidades vendidas
    (movimientos de salida) × precio_unitario actual.

    Recibe:
        productos  : lista de ProductoAnalitico.
        movimientos: lista de MovimientoAnalitico.

    Devuelve dict {codigo: valor_consumo (float)}, incluyendo los productos
    sin ventas con valor 0.0.
    """
    precios = {p.codigo: p.precio_unitario for p in productos}
    unidades_vendidas: dict = {p.codigo: 0 for p in productos}

    for m in movimientos:
        if m.tipo == "S" and m.codigo_producto in unidades_vendidas:
            unidades_vendidas[m.codigo_producto] += m.cantidad

    return {
        codigo: unidades * precios[codigo]
        for codigo, unidades in unidades_vendidas.items()
    }


def clasificar_abc(productos: list, movimientos: list) -> list:
    """
    Clasifica los productos en A/B/C según su valor de consumo acumulado:
    A hasta el 80%, B hasta el 95%, C el resto.

    Recibe:
        productos  : lista de ProductoAnalitico.
        movimientos: lista de MovimientoAnalitico.

    Devuelve lista de dicts ordenada descendente por valor_consumo:
        [{"codigo": str, "nombre": str, "valor_consumo": float,
          "porcentaje": float, "porcentaje_acumulado": float,
          "clase_abc": "A"|"B"|"C"}, ...]
    """
    if not productos:
        raise DatosInsuficientes("No hay productos para clasificar.")

    nombres = {p.codigo: p.nombre for p in productos}
    valores = valor_consumo_por_producto(productos, movimientos)
    total = sum(valores.values())

    ordenados = sorted(valores.items(), key=lambda item: (-item[1], item[0]))

    resultado = []
    acumulado = 0.0
    for codigo, valor in ordenados:
        acumulado += valor
        porcentaje = (valor / total * 100) if total > 0 else 0.0
        porcentaje_acumulado = (acumulado / total * 100) if total > 0 else 0.0

        if total <= 0:
            clase = "C"
        elif porcentaje_acumulado <= LIMITE_A * 100:
            clase = "A"
        elif porcentaje_acumulado <= LIMITE_B * 100:
            clase = "B"
        else:
            clase = "C"

        resultado.append({
            "codigo": codigo,
            "nombre": nombres[codigo],
            "valor_consumo": round(valor, 2),
            "porcentaje": round(porcentaje, 2),
            "porcentaje_acumulado": round(porcentaje_acumulado, 2),
            "clase_abc": clase,
        })

    return resultado


# ──────────────────────────────────────────────
# XYZ por coeficiente de variación de la demanda mensual
# ──────────────────────────────────────────────

def demanda_mensual_por_producto(movimientos: list, meses: list | None = None) -> dict:
    """
    Unidades vendidas (salidas) por producto y por mes, con 0 en los meses
    del período sin ventas.

    Recibe:
        movimientos: lista de MovimientoAnalitico.
        meses      : lista de (anio, mes) a incluir; si es None, se usa todo
                     el período cubierto por `movimientos`.

    Devuelve dict {codigo: {(anio, mes): unidades, ...}}.
    """
    if meses is None:
        meses = meses_periodo(movimientos)

    series: dict = {}
    for m in movimientos:
        if m.tipo != "S":
            continue
        fecha = datetime.strptime(m.fecha, "%Y-%m-%d").date()
        clave_mes = (fecha.year, fecha.month)
        serie = series.setdefault(m.codigo_producto, {mes: 0 for mes in meses})
        if clave_mes in serie:
            serie[clave_mes] += m.cantidad

    return series


def _coeficiente_variacion(valores: list) -> float:
    """
    Coeficiente de variación (desviación estándar poblacional / media) de
    una serie. Devuelve float('inf') si la media es 0 (sin demanda, por lo
    tanto máxima irregularidad).
    """
    media = statistics.mean(valores)
    if media == 0:
        return float("inf")
    desviacion = statistics.pstdev(valores)
    return desviacion / media


def _clase_xyz(cv: float) -> str:
    if cv < CV_LIMITE_X:
        return "X"
    if cv <= CV_LIMITE_Y:
        return "Y"
    return "Z"


def clasificar_xyz(productos: list, movimientos: list) -> list:
    """
    Clasifica los productos en X/Y/Z según la regularidad de su demanda
    mensual: X (CV < 0.5) regular, Y (0.5-1) variable, Z (> 1) irregular.

    Recibe:
        productos  : lista de ProductoAnalitico.
        movimientos: lista de MovimientoAnalitico.

    Devuelve lista de dicts:
        [{"codigo": str, "nombre": str, "cv_demanda": float,
          "clase_xyz": "X"|"Y"|"Z"}, ...]

    Lanza DatosInsuficientes si no hay movimientos con los que construir
    ningún mes de demanda.
    """
    if not productos:
        raise DatosInsuficientes("No hay productos para clasificar.")

    meses = meses_periodo(movimientos)
    if not meses:
        raise DatosInsuficientes(
            "No hay movimientos suficientes para construir una serie mensual de demanda."
        )

    nombres = {p.codigo: p.nombre for p in productos}
    series = demanda_mensual_por_producto(movimientos, meses)

    resultado = []
    for p in productos:
        valores_mensuales = list(series.get(p.codigo, {mes: 0 for mes in meses}).values())
        cv = _coeficiente_variacion(valores_mensuales)
        resultado.append({
            "codigo": p.codigo,
            "nombre": nombres[p.codigo],
            "cv_demanda": None if cv == float("inf") else round(cv, 3),
            "clase_xyz": _clase_xyz(cv),
        })

    return sorted(resultado, key=lambda r: r["codigo"])


# ──────────────────────────────────────────────
# Matriz combinada ABC-XYZ
# ──────────────────────────────────────────────

def clasificar_abc_xyz(productos: list, movimientos: list) -> list:
    """
    Combina clasificar_abc y clasificar_xyz en una sola matriz de 9 celdas,
    cada una con su recomendación de manejo de inventario.

    Recibe:
        productos  : lista de ProductoAnalitico.
        movimientos: lista de MovimientoAnalitico.

    Devuelve lista de dicts ordenada descendente por valor_consumo:
        [{"codigo": str, "nombre": str, "valor_consumo": float,
          "clase_abc": "A"|"B"|"C", "cv_demanda": float|None,
          "clase_xyz": "X"|"Y"|"Z", "celda": str (p. ej. "AX"),
          "recomendacion": str}, ...]
    """
    abc = {r["codigo"]: r for r in clasificar_abc(productos, movimientos)}
    xyz = {r["codigo"]: r for r in clasificar_xyz(productos, movimientos)}

    resultado = []
    for codigo, r_abc in abc.items():
        r_xyz = xyz[codigo]
        celda = r_abc["clase_abc"] + r_xyz["clase_xyz"]
        resultado.append({
            "codigo": codigo,
            "nombre": r_abc["nombre"],
            "valor_consumo": r_abc["valor_consumo"],
            "clase_abc": r_abc["clase_abc"],
            "cv_demanda": r_xyz["cv_demanda"],
            "clase_xyz": r_xyz["clase_xyz"],
            "celda": celda,
            "recomendacion": MATRIZ_RECOMENDACIONES[(r_abc["clase_abc"], r_xyz["clase_xyz"])],
        })

    return sorted(resultado, key=lambda r: (-r["valor_consumo"], r["codigo"]))


def resumen_matriz(clasificacion: list) -> list:
    """
    Agrupa una clasificación ABC-XYZ ya calculada por celda, para mostrarla
    como una matriz de 3×3.

    Recibe:
        clasificacion: salida de clasificar_abc_xyz.

    Devuelve lista de dicts, una por celda con al menos un producto:
        [{"celda": str, "clase_abc": str, "clase_xyz": str,
          "num_productos": int, "valor_consumo_total": float,
          "recomendacion": str}, ...]
    """
    celdas: dict = {}
    for r in clasificacion:
        celda = celdas.setdefault(r["celda"], {
            "celda": r["celda"],
            "clase_abc": r["clase_abc"],
            "clase_xyz": r["clase_xyz"],
            "num_productos": 0,
            "valor_consumo_total": 0.0,
            "recomendacion": r["recomendacion"],
        })
        celda["num_productos"] += 1
        celda["valor_consumo_total"] += r["valor_consumo"]

    for celda in celdas.values():
        celda["valor_consumo_total"] = round(celda["valor_consumo_total"], 2)

    return sorted(celdas.values(), key=lambda c: (c["clase_abc"], c["clase_xyz"]))
