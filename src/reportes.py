"""
Reportes estadísticos para FerroAnalytics (Fase I).
Todas las funciones reciben listas de objetos del modelo y devuelven
estructuras de datos listas para presentar; no hacen I/O.
"""

from datetime import date, datetime, timedelta

from src.modelos import CategoriaAnalitica, MovimientoAnalitico, ProductoAnalitico


# ──────────────────────────────────────────────
# Helpers internos
# ──────────────────────────────────────────────

def _indice_categorias(categorias: list) -> dict:
    """Devuelve {id: nombre} a partir de la lista de CategoriaAnalitica."""
    return {c.id: c.nombre for c in categorias}


def _parsear_fecha(cadena: str) -> date:
    """Convierte 'AAAA-MM-DD' a date; devuelve date.min si el formato falla."""
    try:
        return datetime.strptime(cadena, "%Y-%m-%d").date()
    except ValueError:
        return date.min


# ──────────────────────────────────────────────
# Reporte 1: Stock total por categoría
# ──────────────────────────────────────────────

def stock_por_categoria(productos: list, categorias: list) -> list:
    """
    Calcula el stock total (unidades) y el valor inmovilizado por categoría.

    Recibe:
        productos  : lista de ProductoAnalitico.
        categorias : lista de CategoriaAnalitica.

    Devuelve lista de dicts ordenada descendente por stock_total:
        [{"id_categoria": int, "nombre": str,
          "num_productos": int, "stock_total": int,
          "valor_total": float}, ...]
    """
    nombres = _indice_categorias(categorias)
    acumulado: dict[int, dict] = {}

    for p in productos:
        if p.id_categoria not in acumulado:
            acumulado[p.id_categoria] = {
                "id_categoria": p.id_categoria,
                "nombre": nombres.get(p.id_categoria, f"Categoría {p.id_categoria}"),
                "num_productos": 0,
                "stock_total": 0,
                "valor_total": 0.0,
            }
        acumulado[p.id_categoria]["num_productos"] += 1
        acumulado[p.id_categoria]["stock_total"] += p.stock_actual
        acumulado[p.id_categoria]["valor_total"] += p.stock_actual * p.precio_unitario

    return sorted(acumulado.values(), key=lambda r: r["stock_total"], reverse=True)


# ──────────────────────────────────────────────
# Reporte 2: Top N productos con stock inmovilizado
# ──────────────────────────────────────────────

def top_inmovilizado(
    productos: list,
    movimientos: list,
    n: int = 10,
    dias: int = 90,
) -> list:
    """
    Devuelve los N productos con mayor valor de stock inmovilizado,
    entendiendo por «inmovilizado» aquellos sin movimientos de salida
    en los últimos `dias` días.

    Recibe:
        productos  : lista de ProductoAnalitico.
        movimientos: lista de MovimientoAnalitico.
        n          : cantidad de productos a devolver (por defecto 10).
        dias       : ventana temporal en días (por defecto 90).

    Devuelve lista de dicts ordenada descendente por valor_inmovilizado:
        [{"codigo": str, "nombre": str, "id_categoria": int,
          "stock_actual": int, "precio_unitario": float,
          "valor_inmovilizado": float,
          "ultima_salida": str | None}, ...]
    """
    corte = date.today() - timedelta(days=dias)

    # Última salida por producto
    ultima_salida: dict[str, date] = {}
    for m in movimientos:
        if m.tipo == "S":
            fecha_mov = _parsear_fecha(m.fecha)
            if m.codigo_producto not in ultima_salida or fecha_mov > ultima_salida[m.codigo_producto]:
                ultima_salida[m.codigo_producto] = fecha_mov

    inmovilizados = []
    for p in productos:
        salida = ultima_salida.get(p.codigo)
        if salida is None or salida < corte:
            inmovilizados.append({
                "codigo": p.codigo,
                "nombre": p.nombre,
                "id_categoria": p.id_categoria,
                "stock_actual": p.stock_actual,
                "precio_unitario": p.precio_unitario,
                "valor_inmovilizado": round(p.stock_actual * p.precio_unitario, 2),
                "ultima_salida": salida.isoformat() if salida else None,
            })

    return sorted(inmovilizados, key=lambda r: r["valor_inmovilizado"], reverse=True)[:n]


# ──────────────────────────────────────────────
# Reporte 3: Ventas mensuales por categoría
# ──────────────────────────────────────────────

def ventas_mensuales_por_categoria(
    movimientos: list,
    productos: list,
    categorias: list,
) -> list:
    """
    Calcula las unidades vendidas (salidas) por mes y categoría.

    Recibe:
        movimientos: lista de MovimientoAnalitico.
        productos  : lista de ProductoAnalitico.
        categorias : lista de CategoriaAnalitica.

    Devuelve lista de dicts ordenada por (anio, mes, nombre_categoria):
        [{"anio": int, "mes": int, "id_categoria": int,
          "nombre_categoria": str, "unidades": int}, ...]
    """
    cat_por_producto = {p.codigo: p.id_categoria for p in productos}
    nombres = _indice_categorias(categorias)

    # Clave: (anio, mes, id_categoria)
    acumulado: dict[tuple, int] = {}

    for m in movimientos:
        if m.tipo != "S":
            continue
        fecha = _parsear_fecha(m.fecha)
        if fecha == date.min:
            continue
        id_cat = cat_por_producto.get(m.codigo_producto)
        if id_cat is None:
            continue
        clave = (fecha.year, fecha.month, id_cat)
        acumulado[clave] = acumulado.get(clave, 0) + m.cantidad

    resultado = [
        {
            "anio": anio,
            "mes": mes,
            "id_categoria": id_cat,
            "nombre_categoria": nombres.get(id_cat, f"Categoría {id_cat}"),
            "unidades": unidades,
        }
        for (anio, mes, id_cat), unidades in acumulado.items()
    ]

    return sorted(resultado, key=lambda r: (r["anio"], r["mes"], r["nombre_categoria"]))


# ──────────────────────────────────────────────
# Reporte 4: Alertas de stock bajo
# ──────────────────────────────────────────────

def alertas_stock_bajo(productos: list, umbral: int | None = None) -> list:
    """
    Lista los productos cuyo stock_actual está por debajo del mínimo.

    Recibe:
        productos: lista de ProductoAnalitico.
        umbral   : si se indica, se usa como mínimo para todos los productos;
                   si es None, se usa el stock_minimo de cada producto.

    Devuelve lista de dicts ordenada ascendente por diferencia (más críticos primero):
        [{"codigo": str, "nombre": str, "id_categoria": int,
          "stock_actual": int, "minimo": int, "diferencia": int}, ...]
    """
    alertas = []
    for p in productos:
        minimo = umbral if umbral is not None else p.stock_minimo
        if p.stock_actual < minimo:
            alertas.append({
                "codigo": p.codigo,
                "nombre": p.nombre,
                "id_categoria": p.id_categoria,
                "stock_actual": p.stock_actual,
                "minimo": minimo,
                "diferencia": p.stock_actual - minimo,   # siempre negativo aquí
            })

    return sorted(alertas, key=lambda r: r["diferencia"])
