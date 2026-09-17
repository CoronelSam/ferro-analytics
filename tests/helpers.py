"""Helpers para construir CSV de prueba y subirlos a la API en los tests."""

from datetime import date


def csv_categorias(filas: list[tuple[int, str]]) -> str:
    """Arma el contenido de un categorias.csv a partir de (id, nombre)."""
    lineas = ["id,nombre"] + [f"{id_},{nombre}" for id_, nombre in filas]
    return "\n".join(lineas) + "\n"


def csv_productos(filas: list[tuple]) -> str:
    """Arma productos.csv a partir de (codigo, nombre, id_categoria,
    precio_unitario, stock_actual, stock_minimo)."""
    lineas = ["codigo,nombre,id_categoria,precio_unitario,stock_actual,stock_minimo"]
    lineas += [
        f"{codigo},{nombre},{id_categoria},{precio_unitario},{stock_actual},{stock_minimo}"
        for codigo, nombre, id_categoria, precio_unitario, stock_actual, stock_minimo in filas
    ]
    return "\n".join(lineas) + "\n"


def csv_movimientos(filas: list[tuple]) -> str:
    """Arma movimientos.csv a partir de (id_movimiento, codigo_producto,
    tipo, cantidad, fecha)."""
    lineas = ["id_movimiento,codigo_producto,tipo,cantidad,fecha"]
    lineas += [
        f"{id_movimiento},{codigo_producto},{tipo},{cantidad},{fecha}"
        for id_movimiento, codigo_producto, tipo, cantidad, fecha in filas
    ]
    return "\n".join(lineas) + "\n"


def subir_csv(cliente, entidad: str, nombre_archivo: str, contenido: str):
    """POST /api/importar/{entidad} con `contenido` como archivo subido."""
    return cliente.post(
        f"/api/importar/{entidad}",
        files={"archivo": (nombre_archivo, contenido.encode("utf-8"), "text/csv")},
    )


def meses_hacia_atras(cantidad: int, dia: int = 5, terminando_hace_meses: int = 2) -> list[str]:
    """
    Devuelve `cantidad` fechas mensuales consecutivas (AAAA-MM-DD, día fijo
    `dia`), en orden cronológico, terminando `terminando_hace_meses` meses
    antes de hoy. El margen evita que la fecha final choque con la
    validación de "fecha no futura" del importador (que usa date.today()
    real, no la fecha de referencia de la Fase II).
    """
    anio, mes = date.today().year, date.today().month
    for _ in range(terminando_hace_meses):
        mes -= 1
        if mes < 1:
            mes, anio = 12, anio - 1

    meses = []
    for _ in range(cantidad):
        meses.append((anio, mes))
        mes -= 1
        if mes < 1:
            mes, anio = 12, anio - 1
    meses.reverse()

    return [date(anio_mes[0], anio_mes[1], dia).isoformat() for anio_mes in meses]
