"""
Predicción de demanda para FerroAnalytics (Fase II).

Construye series mensuales de demanda por categoría y por producto, compara
cuatro modelos de pronóstico mediante backtesting (MAE y MAPE), y calcula el
punto de reorden y el stock de seguridad de un producto a partir de su
demanda diaria observada.

Se comparan tres modelos base (ingenuo, media móvil, suavizado exponencial
simple) contra una regresión con tendencia y estacionalidad mensual; esta
última necesita más historial (ver MINIMO_MESES_HISTORIAL) porque estima
una tendencia más 11 factores estacionales.

Como en clasificacion.py, la fecha de referencia es la del último
movimiento registrado, no date.today().
"""

import math
import statistics
from datetime import datetime, timedelta

import numpy as np
from sklearn.linear_model import LinearRegression

from src.clasificacion import (
    clasificar_abc_xyz,
    demanda_mensual_por_producto,
    meses_periodo,
)
from src.excepciones import DatosInsuficientes

# La regresión estima 1 (tendencia) + 11 (dummies de mes) + 1 (intercepto)
# = 13 parámetros; se exige margen para que la última quede con demanda
# real a la que pronosticar en vez de solo memorizar la serie.
MINIMO_MESES_HISTORIAL = 15
MINIMO_MESES_CON_DATOS = 6

VENTANA_MEDIA_MOVIL = 3
ALPHA_SUAVIZADO = 0.3


# ──────────────────────────────────────────────
# Series mensuales
# ──────────────────────────────────────────────

def serie_mensual_producto(movimientos: list, codigo: str, meses: list | None = None) -> list:
    """
    Unidades vendidas por mes de un producto, 0 en los meses sin ventas.

    Recibe:
        movimientos: lista de MovimientoAnalitico.
        codigo     : código del producto.
        meses      : lista de (anio, mes) a incluir; si es None, se usa todo
                     el período cubierto por `movimientos`.

    Devuelve una lista de unidades, en el mismo orden que `meses`.
    """
    if meses is None:
        meses = meses_periodo(movimientos)
    series = demanda_mensual_por_producto(movimientos, meses)
    serie = series.get(codigo, {mes: 0 for mes in meses})
    return [serie[mes] for mes in meses]


def serie_mensual_categoria(
    movimientos: list,
    productos: list,
    id_categoria: int,
    meses: list | None = None,
) -> list:
    """
    Unidades vendidas por mes de todos los productos de una categoría,
    0 en los meses sin ventas.

    Recibe:
        movimientos : lista de MovimientoAnalitico.
        productos   : lista de ProductoAnalitico.
        id_categoria: id de la categoría a agregar.
        meses       : lista de (anio, mes) a incluir; si es None, se usa
                      todo el período cubierto por `movimientos`.

    Devuelve una lista de unidades, en el mismo orden que `meses`.
    """
    if meses is None:
        meses = meses_periodo(movimientos)
    codigos_categoria = {p.codigo for p in productos if p.id_categoria == id_categoria}

    totales = {mes: 0 for mes in meses}
    for m in movimientos:
        if m.tipo != "S" or m.codigo_producto not in codigos_categoria:
            continue
        fecha = datetime.strptime(m.fecha, "%Y-%m-%d").date()
        clave_mes = (fecha.year, fecha.month)
        if clave_mes in totales:
            totales[clave_mes] += m.cantidad

    return [totales[mes] for mes in meses]


def productos_prioritarios(productos: list, movimientos: list) -> list:
    """
    Códigos de los productos clasificados A (alto valor) y X (demanda
    estable): los mejores candidatos para pronosticar por producto en vez
    de solo por categoría.
    """
    clasificacion = clasificar_abc_xyz(productos, movimientos)
    return [r["codigo"] for r in clasificacion if r["celda"] == "AX"]


# ──────────────────────────────────────────────
# Modelos de pronóstico: cada uno recibe una serie mensual sin huecos y
# devuelve una lista de `n` valores futuros.
# ──────────────────────────────────────────────

def pronostico_ingenuo(serie: list, n: int = 1) -> list:
    """Repite el último valor observado los próximos `n` períodos."""
    if not serie:
        raise DatosInsuficientes("La serie está vacía; no hay un último valor que repetir.")
    return [float(serie[-1])] * n


def pronostico_media_movil(serie: list, n: int = 1, ventana: int = VENTANA_MEDIA_MOVIL) -> list:
    """Repite el promedio de los últimos `ventana` períodos los próximos `n`."""
    if len(serie) < ventana:
        raise DatosInsuficientes(
            f"Se necesitan al menos {ventana} períodos para la media móvil (hay {len(serie)})."
        )
    promedio = statistics.mean(serie[-ventana:])
    return [promedio] * n


def pronostico_suavizado_exponencial(serie: list, n: int = 1, alpha: float = ALPHA_SUAVIZADO) -> list:
    """
    Suavizado exponencial simple: nivel_t = alpha·real_t + (1-alpha)·nivel_(t-1).
    El pronóstico es plano: repite el último nivel suavizado los próximos `n`.
    """
    if not serie:
        raise DatosInsuficientes("La serie está vacía; no se puede suavizar.")
    nivel = float(serie[0])
    for valor in serie[1:]:
        nivel = alpha * valor + (1 - alpha) * nivel
    return [nivel] * n


def pronostico_regresion(serie: list, n: int = 1) -> list:
    """
    Regresión lineal con tendencia (índice temporal) y estacionalidad
    mensual (variables dummy según la posición del mes dentro del ciclo
    anual de la propia serie).

    Recibe:
        serie: valores mensuales consecutivos y sin huecos.
        n    : cantidad de períodos futuros a pronosticar.

    Devuelve una lista de `n` valores pronosticados (no negativos).

    Lanza DatosInsuficientes si la serie es muy corta para estimar
    tendencia + 11 factores estacionales de forma no degenerada.
    """
    if len(serie) < MINIMO_MESES_HISTORIAL:
        raise DatosInsuficientes(
            f"Se necesitan al menos {MINIMO_MESES_HISTORIAL} meses de historial para la "
            f"regresión con tendencia y estacionalidad (hay {len(serie)})."
        )

    t = np.arange(len(serie))
    mes_del_ciclo = t % 12
    dummies = np.eye(12)[mes_del_ciclo][:, 1:]   # una columna menos: evita colinealidad con el intercepto
    X = np.column_stack([t, dummies])
    y = np.asarray(serie, dtype=float)

    modelo = LinearRegression()
    modelo.fit(X, y)

    t_futuro = np.arange(len(serie), len(serie) + n)
    dummies_futuro = np.eye(12)[t_futuro % 12][:, 1:]
    X_futuro = np.column_stack([t_futuro, dummies_futuro])

    return [max(0.0, float(v)) for v in modelo.predict(X_futuro)]


MODELOS = {
    "ingenuo": pronostico_ingenuo,
    "media_movil": pronostico_media_movil,
    "suavizado_exponencial": pronostico_suavizado_exponencial,
    "regresion": pronostico_regresion,
}


# ──────────────────────────────────────────────
# Backtesting: MAE y MAPE
# ──────────────────────────────────────────────

def _mae(reales: list, pronosticados: list) -> float:
    return statistics.mean(abs(r - p) for r, p in zip(reales, pronosticados))


def _mape(reales: list, pronosticados: list) -> float | None:
    """
    Error porcentual absoluto medio. Ignora los meses con demanda real 0
    (el porcentaje no está definido); devuelve None si todos lo son.
    """
    errores = [abs(r - p) / r for r, p in zip(reales, pronosticados) if r != 0]
    return statistics.mean(errores) * 100 if errores else None


def backtest(serie: list, modelo, n_prueba: int = 3) -> dict:
    """
    Evalúa un modelo de pronóstico dejando fuera los últimos `n_prueba`
    meses: aplica el modelo sobre el resto de la serie, pronostica esos
    meses y compara contra los valores reales.

    Recibe:
        serie   : valores mensuales consecutivos y sin huecos.
        modelo  : función pronostico_*(serie, n) -> list[float].
        n_prueba: cantidad de meses finales a dejar fuera para probar.

    Devuelve {"mae": float, "mape": float | None}.

    Lanza DatosInsuficientes si no quedan suficientes meses de entrenamiento
    para el modelo indicado.
    """
    if len(serie) <= n_prueba:
        raise DatosInsuficientes(
            f"La serie tiene {len(serie)} meses; no alcanza para dejar {n_prueba} de prueba."
        )
    entrenamiento = serie[:-n_prueba]
    prueba = serie[-n_prueba:]
    pronosticados = modelo(entrenamiento, n=n_prueba)

    mape = _mape(prueba, pronosticados)
    return {
        "mae": round(_mae(prueba, pronosticados), 3),
        "mape": round(mape, 2) if mape is not None else None,
    }


def comparar_modelos(serie: list, n_prueba: int = 3) -> list:
    """
    Compara los cuatro modelos de pronóstico sobre la misma serie mediante
    backtesting, ordenados por MAE ascendente (mejor primero).

    Recibe:
        serie   : valores mensuales consecutivos y sin huecos.
        n_prueba: cantidad de meses finales a dejar fuera para el backtest.

    Devuelve lista de dicts: [{"modelo": str, "mae": float, "mape": float | None}, ...]

    Un modelo sin historial suficiente para evaluarse (p. ej. la regresión
    sobre series cortas) se omite en vez de interrumpir a los demás.
    Lanza DatosInsuficientes si ninguno pudo evaluarse.
    """
    resultados = []
    for nombre, funcion in MODELOS.items():
        try:
            metricas = backtest(serie, funcion, n_prueba=n_prueba)
        except DatosInsuficientes:
            continue
        resultados.append({"modelo": nombre, **metricas})

    if not resultados:
        raise DatosInsuficientes("Ningún modelo pudo evaluarse: la serie es demasiado corta.")

    return sorted(resultados, key=lambda r: r["mae"])


# ──────────────────────────────────────────────
# Punto de reorden y stock de seguridad
# ──────────────────────────────────────────────

def calcular_punto_reorden(
    movimientos: list,
    codigo: str,
    tiempo_entrega_dias: int,
    nivel_servicio: float = 0.95,
) -> dict:
    """
    Calcula el stock de seguridad y el punto de reorden de un producto a
    partir de su demanda diaria observada (incluye los días sin ventas
    dentro de su período de actividad).

    Recibe:
        movimientos        : lista de MovimientoAnalitico.
        codigo              : código del producto.
        tiempo_entrega_dias : tiempo de entrega del proveedor, en días.
        nivel_servicio      : probabilidad deseada de no quedarse sin stock
                               durante el tiempo de entrega (0-1; 0.95 por defecto).

    Devuelve:
        {"demanda_diaria_media": float, "demanda_diaria_desviacion": float,
         "z": float, "stock_seguridad": float, "punto_reorden": float}

    Lanza DatosInsuficientes si el producto no tiene movimientos de salida.
    """
    ventas_por_dia: dict = {}
    for m in movimientos:
        if m.tipo == "S" and m.codigo_producto == codigo:
            fecha = datetime.strptime(m.fecha, "%Y-%m-%d").date()
            ventas_por_dia[fecha] = ventas_por_dia.get(fecha, 0) + m.cantidad

    if not ventas_por_dia:
        raise DatosInsuficientes(f"'{codigo}' no tiene movimientos de salida registrados.")

    inicio, fin = min(ventas_por_dia), max(ventas_por_dia)
    dias_periodo = (fin - inicio).days + 1
    serie_diaria = [ventas_por_dia.get(inicio + timedelta(days=i), 0) for i in range(dias_periodo)]

    media_diaria = statistics.mean(serie_diaria)
    desviacion_diaria = statistics.pstdev(serie_diaria)
    z = statistics.NormalDist().inv_cdf(nivel_servicio)

    stock_seguridad = z * desviacion_diaria * math.sqrt(tiempo_entrega_dias)
    punto_reorden = media_diaria * tiempo_entrega_dias + stock_seguridad

    return {
        "demanda_diaria_media": round(media_diaria, 3),
        "demanda_diaria_desviacion": round(desviacion_diaria, 3),
        "z": round(z, 3),
        "stock_seguridad": round(stock_seguridad, 2),
        "punto_reorden": round(punto_reorden, 2),
    }


# ──────────────────────────────────────────────
# Orquestación: producto y categoría
# ──────────────────────────────────────────────

def _validar_historial(serie: list, contexto: str) -> None:
    if len(serie) < MINIMO_MESES_HISTORIAL:
        raise DatosInsuficientes(
            f"{contexto}: se necesitan al menos {MINIMO_MESES_HISTORIAL} meses de historial "
            f"para pronosticar (hay {len(serie)})."
        )
    meses_con_datos = sum(1 for v in serie if v > 0)
    if meses_con_datos < MINIMO_MESES_CON_DATOS:
        raise DatosInsuficientes(
            f"{contexto}: solo {meses_con_datos} de {len(serie)} meses tienen ventas "
            f"registradas; no alcanza para un pronóstico confiable."
        )


def _siguientes_meses(ultimo_mes: tuple, n: int) -> list:
    """Genera los `n` pares (anio, mes) siguientes a `ultimo_mes`."""
    anio, mes = ultimo_mes
    resultado = []
    for _ in range(n):
        mes += 1
        if mes > 12:
            mes = 1
            anio += 1
        resultado.append((anio, mes))
    return resultado


def pronosticar_producto(
    productos: list,
    movimientos: list,
    codigo: str,
    n: int = 1,
    n_prueba: int = 3,
    tiempo_entrega_dias: int = 7,
    nivel_servicio: float = 0.95,
) -> dict:
    """
    Pronóstico de demanda mensual de un producto: compara los cuatro
    modelos por backtesting, pronostica con el mejor y agrega el punto de
    reorden y el stock de seguridad calculados con su demanda diaria.

    Recibe:
        productos, movimientos: catálogo e historial completos.
        codigo                : código del producto a pronosticar.
        n                     : cantidad de meses futuros a pronosticar.
        n_prueba              : meses finales usados para el backtest.
        tiempo_entrega_dias   : tiempo de entrega del proveedor, en días.
        nivel_servicio        : nivel de servicio deseado (0-1) para el
                                 stock de seguridad.

    Devuelve un dict con "codigo", "meses_pronosticados", "comparacion_modelos",
    "mejor_modelo", "pronostico" y las claves de calcular_punto_reorden().

    Lanza DatosInsuficientes si el historial del producto es muy corto.
    """
    meses = meses_periodo(movimientos)
    serie = serie_mensual_producto(movimientos, codigo, meses)
    _validar_historial(serie, f"Producto '{codigo}'")

    comparacion = comparar_modelos(serie, n_prueba=n_prueba)
    mejor = comparacion[0]["modelo"]
    pronostico = MODELOS[mejor](serie, n=n)
    reorden = calcular_punto_reorden(movimientos, codigo, tiempo_entrega_dias, nivel_servicio)

    return {
        "codigo": codigo,
        "meses_pronosticados": _siguientes_meses(meses[-1], n),
        "comparacion_modelos": comparacion,
        "mejor_modelo": mejor,
        "pronostico": [round(v, 2) for v in pronostico],
        **reorden,
    }


def pronosticar_categoria(
    productos: list,
    movimientos: list,
    categorias: list,
    id_categoria: int,
    n: int = 1,
    n_prueba: int = 3,
) -> dict:
    """
    Pronóstico de demanda mensual de una categoría completa: compara los
    cuatro modelos por backtesting y pronostica con el mejor.

    Recibe:
        productos, movimientos, categorias: catálogo e historial completos.
        id_categoria                      : id de la categoría a pronosticar.
        n                                  : cantidad de meses futuros.
        n_prueba                           : meses finales usados para el backtest.

    Devuelve un dict con "id_categoria", "nombre_categoria",
    "meses_pronosticados", "comparacion_modelos", "mejor_modelo" y "pronostico".

    Lanza DatosInsuficientes si el historial de la categoría es muy corto.
    """
    nombres_cat = {c.id: c.nombre for c in categorias}
    meses = meses_periodo(movimientos)
    serie = serie_mensual_categoria(movimientos, productos, id_categoria, meses)
    _validar_historial(serie, f"Categoría '{nombres_cat.get(id_categoria, id_categoria)}'")

    comparacion = comparar_modelos(serie, n_prueba=n_prueba)
    mejor = comparacion[0]["modelo"]
    pronostico = MODELOS[mejor](serie, n=n)

    return {
        "id_categoria": id_categoria,
        "nombre_categoria": nombres_cat.get(id_categoria, f"Categoría {id_categoria}"),
        "meses_pronosticados": _siguientes_meses(meses[-1], n),
        "comparacion_modelos": comparacion,
        "mejor_modelo": mejor,
        "pronostico": [round(v, 2) for v in pronostico],
    }
