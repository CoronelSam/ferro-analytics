"""
Importador de archivos CSV para FerroAnalytics (Fase I).
Lee, valida y convierte las filas de cada CSV en objetos del modelo.
No escribe en disco: eso corresponde a almacenamiento.py.
"""

import csv
from datetime import date, datetime
from typing import Tuple

from src.modelos import CategoriaAnalitica, MovimientoAnalitico, ProductoAnalitico


# ──────────────────────────────────────────────
# Helpers de validación
# ──────────────────────────────────────────────

def _parsear_fecha(valor: str) -> date:
    """
    Convierte una cadena AAAA-MM-DD a date.
    Lanza ValueError si el formato es incorrecto o la fecha es futura.
    """
    try:
        fecha = datetime.strptime(valor.strip(), "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"Formato de fecha inválido: '{valor}' (se espera AAAA-MM-DD)")
    if fecha > date.today():
        raise ValueError(f"La fecha '{valor}' es futura")
    return fecha


def _validar_entero_no_negativo(valor: str, nombre_campo: str) -> int:
    """Convierte a int y verifica que sea >= 0."""
    try:
        n = int(valor)
    except ValueError:
        raise ValueError(f"'{nombre_campo}' no es un entero: '{valor}'")
    if n < 0:
        raise ValueError(f"'{nombre_campo}' no puede ser negativo: {n}")
    return n


def _validar_float_no_negativo(valor: str, nombre_campo: str) -> float:
    """Convierte a float y verifica que sea >= 0."""
    try:
        f = float(valor)
    except ValueError:
        raise ValueError(f"'{nombre_campo}' no es un número: '{valor}'")
    if f < 0:
        raise ValueError(f"'{nombre_campo}' no puede ser negativo: {f}")
    return f


def _fila_rechazada(numero: int, fila: dict, motivo: str) -> dict:
    """Construye el registro de una fila rechazada."""
    return {"fila": numero, "datos": fila, "motivo": motivo}


# ──────────────────────────────────────────────
# Importadores públicos
# ──────────────────────────────────────────────

def importar_categorias(
    ruta_csv: str,
) -> Tuple[list, list]:
    """
    Lee categorias.csv y valida cada fila.

    Recibe:
        ruta_csv: ruta al archivo CSV con columnas id, nombre.

    Devuelve:
        (aceptadas, rechazadas)
        aceptadas : lista de CategoriaAnalitica válidos.
        rechazadas: lista de dicts {fila, datos, motivo} con filas inválidas.
    """
    aceptadas: list[CategoriaAnalitica] = []
    rechazadas: list[dict] = []
    columnas_requeridas = {"id", "nombre"}

    with open(ruta_csv, newline="", encoding="utf-8") as f:
        lector = csv.DictReader(f)
        _verificar_columnas(lector.fieldnames, columnas_requeridas, ruta_csv)

        for num, fila in enumerate(lector, start=2):
            try:
                id_cat = _validar_entero_no_negativo(fila["id"], "id")
                nombre = fila["nombre"].strip()
                if not nombre:
                    raise ValueError("'nombre' no puede estar vacío")
                aceptadas.append(CategoriaAnalitica(id=id_cat, nombre=nombre))
            except (ValueError, KeyError) as e:
                rechazadas.append(_fila_rechazada(num, dict(fila), str(e)))

    return aceptadas, rechazadas


def importar_productos(
    ruta_csv: str,
) -> Tuple[list, list]:
    """
    Lee productos.csv y valida cada fila.

    Recibe:
        ruta_csv: ruta al archivo CSV con columnas
                  codigo, nombre, id_categoria, precio_unitario,
                  stock_actual, stock_minimo.

    Devuelve:
        (aceptados, rechazados)
        aceptados : lista de ProductoAnalitico válidos.
        rechazados: lista de dicts {fila, datos, motivo} con filas inválidas.
    """
    aceptados: list[ProductoAnalitico] = []
    rechazados: list[dict] = []
    columnas_requeridas = {
        "codigo", "nombre", "id_categoria",
        "precio_unitario", "stock_actual", "stock_minimo",
    }
    hoy = date.today().isoformat()

    with open(ruta_csv, newline="", encoding="utf-8") as f:
        lector = csv.DictReader(f)
        _verificar_columnas(lector.fieldnames, columnas_requeridas, ruta_csv)

        for num, fila in enumerate(lector, start=2):
            try:
                codigo = fila["codigo"].strip()
                if not codigo:
                    raise ValueError("'codigo' no puede estar vacío")
                if len(codigo) > 10:
                    raise ValueError(f"'codigo' excede 10 caracteres: '{codigo}'")

                nombre = fila["nombre"].strip()
                if not nombre:
                    raise ValueError("'nombre' no puede estar vacío")

                id_categoria = _validar_entero_no_negativo(fila["id_categoria"], "id_categoria")
                precio_unitario = _validar_float_no_negativo(fila["precio_unitario"], "precio_unitario")
                stock_actual = _validar_entero_no_negativo(fila["stock_actual"], "stock_actual")
                stock_minimo = _validar_entero_no_negativo(fila["stock_minimo"], "stock_minimo")

                aceptados.append(ProductoAnalitico(
                    codigo=codigo,
                    nombre=nombre,
                    id_categoria=id_categoria,
                    precio_unitario=precio_unitario,
                    stock_actual=stock_actual,
                    stock_minimo=stock_minimo,
                    fecha_ultima_actualizacion=hoy,
                ))
            except (ValueError, KeyError) as e:
                rechazados.append(_fila_rechazada(num, dict(fila), str(e)))

    return aceptados, rechazados


def importar_movimientos(
    ruta_csv: str,
    codigos_validos: set,
    ids_existentes: set,
) -> Tuple[list, list]:
    """
    Lee movimientos.csv y valida cada fila.

    Recibe:
        ruta_csv       : ruta al CSV con columnas id_movimiento, codigo_producto,
                         tipo, cantidad, fecha.
        codigos_validos: conjunto de códigos de producto ya almacenados.
        ids_existentes : conjunto de id_movimiento ya almacenados (para detectar
                         duplicados dentro del mismo archivo y contra el binario).

    Devuelve:
        (aceptados, rechazados)
        aceptados : lista de MovimientoAnalitico válidos.
        rechazados: lista de dicts {fila, datos, motivo} con filas inválidas.

    Nota: ids_existentes se actualiza en memoria durante la lectura para detectar
    duplicados dentro del mismo archivo CSV.
    """
    aceptados: list[MovimientoAnalitico] = []
    rechazados: list[dict] = []
    columnas_requeridas = {
        "id_movimiento", "codigo_producto", "tipo", "cantidad", "fecha",
    }

    with open(ruta_csv, newline="", encoding="utf-8") as f:
        lector = csv.DictReader(f)
        _verificar_columnas(lector.fieldnames, columnas_requeridas, ruta_csv)

        for num, fila in enumerate(lector, start=2):
            try:
                id_mov = _validar_entero_no_negativo(fila["id_movimiento"], "id_movimiento")
                if id_mov in ids_existentes:
                    raise ValueError(f"id_movimiento duplicado: {id_mov}")

                codigo = fila["codigo_producto"].strip()
                if not codigo:
                    raise ValueError("'codigo_producto' no puede estar vacío")
                if codigo not in codigos_validos:
                    raise ValueError(f"codigo_producto '{codigo}' no existe en el inventario")

                tipo = fila["tipo"].strip().upper()
                if tipo not in MovimientoAnalitico.TIPOS_VALIDOS:
                    raise ValueError(f"'tipo' debe ser E o S, recibido: '{tipo}'")

                cantidad = _validar_entero_no_negativo(fila["cantidad"], "cantidad")
                _parsear_fecha(fila["fecha"])   # valida formato y que no sea futura
                fecha = fila["fecha"].strip()

                ids_existentes.add(id_mov)
                aceptados.append(MovimientoAnalitico(
                    id_movimiento=id_mov,
                    codigo_producto=codigo,
                    tipo=tipo,
                    cantidad=cantidad,
                    fecha=fecha,
                ))
            except (ValueError, KeyError) as e:
                rechazados.append(_fila_rechazada(num, dict(fila), str(e)))

    return aceptados, rechazados


# ──────────────────────────────────────────────
# Helpers internos
# ──────────────────────────────────────────────

def _verificar_columnas(
    fieldnames: list | None,
    requeridas: set,
    ruta: str,
) -> None:
    """Lanza ValueError si faltan columnas obligatorias en el CSV."""
    presentes = set(fieldnames or [])
    faltantes = requeridas - presentes
    if faltantes:
        raise ValueError(
            f"El archivo '{ruta}' no tiene las columnas requeridas: {sorted(faltantes)}"
        )
