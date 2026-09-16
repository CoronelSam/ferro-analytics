"""
Índices binarios para FerroAnalytics (Fase II).

Cada índice es un archivo .idx propio, ordenado por su clave, que asocia
clave → posición (offset en bytes) del registro correspondiente en el .dat.
Permite ubicar un registro con búsqueda binaria en vez de leer todo el
archivo, y actualizarlo con `seek` en vez de reescribir el binario completo.

Índices:
    productos.idx         código (10s)        → posición (i)   clave única
    movimientos.idx        id_movimiento (i)   → posición (i)   clave única
    movimientos_fecha.idx  fecha (10s)         → posición (i)   clave repetible

La ruta de cada .idx se deriva de la ruta del .dat correspondiente (mismo
directorio), para que respete FERRO_BINARIOS igual que almacenamiento.py.
"""

import bisect
import os
import struct

from src.excepciones import ArchivoCorrupto, ErrorAlmacenamiento
from src.almacenamiento import RUTA_MOVIMIENTOS, RUTA_PRODUCTOS
from src.modelos import TAMANO_MOVIMIENTO, TAMANO_PRODUCTO

FORMATO_INDICE_PRODUCTO = "<10si"
TAMANO_INDICE_PRODUCTO = struct.calcsize(FORMATO_INDICE_PRODUCTO)

FORMATO_INDICE_MOVIMIENTO = "<ii"
TAMANO_INDICE_MOVIMIENTO = struct.calcsize(FORMATO_INDICE_MOVIMIENTO)

FORMATO_INDICE_FECHA = "<10si"
TAMANO_INDICE_FECHA = struct.calcsize(FORMATO_INDICE_FECHA)


def _ruta_indice(ruta_dat: str, sufijo: str = "") -> str:
    """Deriva la ruta del .idx a partir de la ruta del .dat (mismo directorio)."""
    base, _ = os.path.splitext(ruta_dat)
    return f"{base}{sufijo}.idx"


RUTA_INDICE_PRODUCTOS = _ruta_indice(RUTA_PRODUCTOS)
RUTA_INDICE_MOVIMIENTOS = _ruta_indice(RUTA_MOVIMIENTOS)
RUTA_INDICE_MOVIMIENTOS_FECHA = _ruta_indice(RUTA_MOVIMIENTOS, "_fecha")


def _codificar_texto(valor: str, longitud: int) -> bytes:
    return valor.encode("utf-8").ljust(longitud)[:longitud]


def _decodificar_texto(valor: bytes) -> str:
    return valor.decode("utf-8").rstrip("\x00").strip()


# ──────────────────────────────────────────────
# E/S genérica de un archivo de índice
# ──────────────────────────────────────────────

def _num_entradas(ruta: str, tamano: int) -> int:
    """Cantidad de registros de tamaño fijo `tamano` en `ruta` (0 si no existe)."""
    if not os.path.exists(ruta):
        return 0
    tamano_archivo = os.path.getsize(ruta)
    if tamano_archivo % tamano != 0:
        raise ArchivoCorrupto(
            f"'{ruta}' tiene un tamaño ({tamano_archivo} bytes) que no es "
            f"múltiplo del tamaño de registro ({tamano} bytes)."
        )
    return tamano_archivo // tamano


def _leer_indice(ruta: str, tamano: int, formato: str) -> list:
    """Lee todas las entradas (clave, posicion) de un archivo de índice, en orden."""
    n = _num_entradas(ruta, tamano)
    if n == 0:
        return []
    entradas = []
    try:
        with open(ruta, "rb") as f:
            for _ in range(n):
                clave, posicion = struct.unpack(formato, f.read(tamano))
                entradas.append((clave, posicion))
    except (OSError, struct.error) as e:
        raise ArchivoCorrupto(f"No se pudo leer el índice '{ruta}': {e}") from e
    return entradas


def _escribir_indice(ruta: str, entradas: list, formato: str) -> None:
    """Escribe la lista completa de entradas (clave, posicion), ya codificadas y ordenadas."""
    directorio = os.path.dirname(ruta)
    if directorio:
        os.makedirs(directorio, exist_ok=True)
    try:
        with open(ruta, "wb") as f:
            for clave, posicion in entradas:
                f.write(struct.pack(formato, clave, posicion))
    except OSError as e:
        raise ErrorAlmacenamiento(f"No se pudo escribir el índice '{ruta}': {e}") from e


def _buscar_en_archivo(ruta: str, tamano: int, formato: str, clave) -> int | None:
    """
    Búsqueda binaria directamente sobre el archivo de índice, sin cargarlo
    en memoria: en cada paso hace `seek` a la entrada intermedia.

    Devuelve la posición asociada a `clave`, o None si no está indexada.
    """
    n = _num_entradas(ruta, tamano)
    if n == 0:
        return None
    try:
        with open(ruta, "rb") as f:
            lo, hi = 0, n - 1
            while lo <= hi:
                medio = (lo + hi) // 2
                f.seek(medio * tamano)
                clave_leida, posicion = struct.unpack(formato, f.read(tamano))
                if clave_leida == clave:
                    return posicion
                if clave_leida < clave:
                    lo = medio + 1
                else:
                    hi = medio - 1
    except (OSError, struct.error) as e:
        raise ArchivoCorrupto(f"No se pudo leer el índice '{ruta}': {e}") from e
    return None


# ──────────────────────────────────────────────
# Índice de productos (por código)
# ──────────────────────────────────────────────

def leer_indice_productos(ruta_dat: str = RUTA_PRODUCTOS) -> list:
    """Devuelve [(codigo: str, posicion: int), ...] ordenado por código."""
    entradas = _leer_indice(_ruta_indice(ruta_dat), TAMANO_INDICE_PRODUCTO, FORMATO_INDICE_PRODUCTO)
    return [(_decodificar_texto(c), p) for c, p in entradas]


def construir_indice_productos(ruta_dat: str = RUTA_PRODUCTOS) -> int:
    """
    Reconstruye productos.idx a partir de productos.dat, ordenado por código.

    Devuelve la cantidad de entradas escritas.
    """
    from src.almacenamiento import leer_productos

    productos = leer_productos(ruta_dat)
    entradas = sorted(
        ((_codificar_texto(p.codigo, 10), i * TAMANO_PRODUCTO) for i, p in enumerate(productos)),
        key=lambda e: e[0],
    )
    _escribir_indice(_ruta_indice(ruta_dat), entradas, FORMATO_INDICE_PRODUCTO)
    return len(entradas)


def obtener_indice_productos_sincronizado(ruta_dat: str = RUTA_PRODUCTOS) -> list:
    """
    Devuelve [(codigo, posicion), ...], reconstruyendo primero productos.idx
    si está corrupto o su número de entradas no coincide con productos.dat
    (por ejemplo, si el .idx no existía todavía o quedó desactualizado).
    """
    try:
        entradas = leer_indice_productos(ruta_dat)
    except ArchivoCorrupto:
        construir_indice_productos(ruta_dat)
        return leer_indice_productos(ruta_dat)

    if len(entradas) != _num_entradas(ruta_dat, TAMANO_PRODUCTO):
        construir_indice_productos(ruta_dat)
        return leer_indice_productos(ruta_dat)
    return entradas


def actualizar_indice_productos(cambios: dict, ruta_dat: str = RUTA_PRODUCTOS) -> None:
    """
    Aplica varios cambios (codigo → posicion) al índice en una sola
    operación y lo reescribe ordenado. Se usa tras un upsert por lotes en
    productos.dat, para no reescribir el índice una vez por producto.
    """
    entradas = dict(leer_indice_productos(ruta_dat))
    entradas.update(cambios)
    codificadas = sorted(
        ((_codificar_texto(c, 10), p) for c, p in entradas.items()),
        key=lambda e: e[0],
    )
    _escribir_indice(_ruta_indice(ruta_dat), codificadas, FORMATO_INDICE_PRODUCTO)


def buscar_producto(codigo: str, ruta_dat: str = RUTA_PRODUCTOS) -> int | None:
    """
    Ubica `codigo` en productos.idx mediante búsqueda binaria sobre el
    archivo (sin leerlo completo).

    Devuelve la posición (offset en bytes) del registro en productos.dat,
    o None si el código no está indexado.
    """
    return _buscar_en_archivo(
        _ruta_indice(ruta_dat), TAMANO_INDICE_PRODUCTO, FORMATO_INDICE_PRODUCTO,
        _codificar_texto(codigo, 10),
    )


# ──────────────────────────────────────────────
# Índice de movimientos por id_movimiento
# ──────────────────────────────────────────────

def leer_indice_movimientos(ruta_dat: str = RUTA_MOVIMIENTOS) -> list:
    """Devuelve [(id_movimiento: int, posicion: int), ...] ordenado por id."""
    return _leer_indice(_ruta_indice(ruta_dat), TAMANO_INDICE_MOVIMIENTO, FORMATO_INDICE_MOVIMIENTO)


def construir_indice_movimientos(ruta_dat: str = RUTA_MOVIMIENTOS) -> int:
    """
    Reconstruye movimientos.idx (por id_movimiento) a partir de movimientos.dat.

    Devuelve la cantidad de entradas escritas.
    """
    from src.almacenamiento import leer_movimientos

    movimientos = leer_movimientos(ruta_dat)
    entradas = sorted(
        ((m.id_movimiento, i * TAMANO_MOVIMIENTO) for i, m in enumerate(movimientos)),
        key=lambda e: e[0],
    )
    _escribir_indice(_ruta_indice(ruta_dat), entradas, FORMATO_INDICE_MOVIMIENTO)
    return len(entradas)


def obtener_indice_movimientos_sincronizado(ruta_dat: str = RUTA_MOVIMIENTOS) -> list:
    """
    Devuelve [(id_movimiento, posicion), ...], reconstruyendo primero
    movimientos.idx si está corrupto o desincronizado con movimientos.dat.
    """
    try:
        entradas = leer_indice_movimientos(ruta_dat)
    except ArchivoCorrupto:
        construir_indice_movimientos(ruta_dat)
        return leer_indice_movimientos(ruta_dat)

    if len(entradas) != _num_entradas(ruta_dat, TAMANO_MOVIMIENTO):
        construir_indice_movimientos(ruta_dat)
        return leer_indice_movimientos(ruta_dat)
    return entradas


def agregar_indice_movimientos(nuevas_entradas: list, ruta_dat: str = RUTA_MOVIMIENTOS) -> None:
    """
    Agrega (id_movimiento, posicion) al índice y lo reescribe ordenado.
    Se usa tras agregar registros al final de movimientos.dat.
    """
    entradas = leer_indice_movimientos(ruta_dat)
    entradas.extend(nuevas_entradas)
    entradas.sort(key=lambda e: e[0])
    _escribir_indice(_ruta_indice(ruta_dat), entradas, FORMATO_INDICE_MOVIMIENTO)


def buscar_movimiento(id_movimiento: int, ruta_dat: str = RUTA_MOVIMIENTOS) -> int | None:
    """
    Ubica `id_movimiento` en movimientos.idx mediante búsqueda binaria.

    Devuelve la posición (offset en bytes) del registro en movimientos.dat,
    o None si no está indexado.
    """
    return _buscar_en_archivo(
        _ruta_indice(ruta_dat), TAMANO_INDICE_MOVIMIENTO, FORMATO_INDICE_MOVIMIENTO,
        id_movimiento,
    )


# ──────────────────────────────────────────────
# Índice de movimientos por fecha (clave no única)
# ──────────────────────────────────────────────

def leer_indice_movimientos_fecha(ruta_dat: str = RUTA_MOVIMIENTOS) -> list:
    """Devuelve [(fecha: str, posicion: int), ...] ordenado por (fecha, posición)."""
    entradas = _leer_indice(_ruta_indice(ruta_dat, "_fecha"), TAMANO_INDICE_FECHA, FORMATO_INDICE_FECHA)
    return [(_decodificar_texto(c), p) for c, p in entradas]


def construir_indice_movimientos_fecha(ruta_dat: str = RUTA_MOVIMIENTOS) -> int:
    """
    Reconstruye movimientos_fecha.idx a partir de movimientos.dat, ordenado
    por (fecha, posición).

    Devuelve la cantidad de entradas escritas.
    """
    from src.almacenamiento import leer_movimientos

    movimientos = leer_movimientos(ruta_dat)
    entradas = sorted(
        ((m.fecha, i * TAMANO_MOVIMIENTO) for i, m in enumerate(movimientos)),
        key=lambda e: (e[0], e[1]),
    )
    codificadas = [(_codificar_texto(f, 10), p) for f, p in entradas]
    _escribir_indice(_ruta_indice(ruta_dat, "_fecha"), codificadas, FORMATO_INDICE_FECHA)
    return len(entradas)


def obtener_indice_movimientos_fecha_sincronizado(ruta_dat: str = RUTA_MOVIMIENTOS) -> list:
    """
    Devuelve [(fecha, posicion), ...], reconstruyendo primero
    movimientos_fecha.idx si está corrupto o desincronizado con movimientos.dat.
    """
    try:
        entradas = leer_indice_movimientos_fecha(ruta_dat)
    except ArchivoCorrupto:
        construir_indice_movimientos_fecha(ruta_dat)
        return leer_indice_movimientos_fecha(ruta_dat)

    if len(entradas) != _num_entradas(ruta_dat, TAMANO_MOVIMIENTO):
        construir_indice_movimientos_fecha(ruta_dat)
        return leer_indice_movimientos_fecha(ruta_dat)
    return entradas


def agregar_indice_movimientos_fecha(nuevas_entradas: list, ruta_dat: str = RUTA_MOVIMIENTOS) -> None:
    """
    Agrega (fecha, posicion) al índice y lo reescribe ordenado por
    (fecha, posición). Se usa tras agregar registros al final de movimientos.dat.
    """
    entradas = leer_indice_movimientos_fecha(ruta_dat)
    entradas.extend(nuevas_entradas)
    entradas.sort(key=lambda e: (e[0], e[1]))
    codificadas = [(_codificar_texto(f, 10), p) for f, p in entradas]
    _escribir_indice(_ruta_indice(ruta_dat, "_fecha"), codificadas, FORMATO_INDICE_FECHA)


def buscar_movimientos_por_fecha(
    fecha_desde: str,
    fecha_hasta: str,
    ruta_dat: str = RUTA_MOVIMIENTOS,
) -> list:
    """
    Ubica, con búsqueda binaria, el inicio del rango [fecha_desde, fecha_hasta]
    en movimientos_fecha.idx.

    Devuelve la lista de posiciones (offsets en movimientos.dat) de los
    movimientos cuya fecha cae en ese rango, en orden de fecha.
    """
    entradas = leer_indice_movimientos_fecha(ruta_dat)
    i = bisect.bisect_left(entradas, fecha_desde, key=lambda e: e[0])
    posiciones = []
    while i < len(entradas) and entradas[i][0] <= fecha_hasta:
        posiciones.append(entradas[i][1])
        i += 1
    return posiciones


# ──────────────────────────────────────────────
# Reconstrucción completa
# ──────────────────────────────────────────────

def reconstruir_indices(
    ruta_productos: str = RUTA_PRODUCTOS,
    ruta_movimientos: str = RUTA_MOVIMIENTOS,
) -> dict:
    """
    Reconstruye productos.idx, movimientos.idx y movimientos_fecha.idx a
    partir de los .dat actuales. Útil tras detectar un índice corrupto o
    faltante, o para regenerarlos manualmente.

    Devuelve un dict con la cantidad de entradas escritas en cada índice.
    """
    return {
        "productos": construir_indice_productos(ruta_productos),
        "movimientos": construir_indice_movimientos(ruta_movimientos),
        "movimientos_fecha": construir_indice_movimientos_fecha(ruta_movimientos),
    }
