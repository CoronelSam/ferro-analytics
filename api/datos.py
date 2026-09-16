"""
Caché en memoria de productos, categorías y movimientos.
Evita releer los .dat en cada request; se recarga al iniciar la API
y tras cada importación exitosa (ver api/rutas/inventario.py).
"""

from src import almacenamiento as alm

_cache: dict[str, list] = {}


def cargar() -> None:
    """Lee los tres binarios y reemplaza el contenido de la caché."""
    _cache["productos"] = alm.leer_productos()
    _cache["categorias"] = alm.leer_categorias()
    _cache["movimientos"] = alm.leer_movimientos()


def productos() -> list:
    return _cache["productos"]


def categorias() -> list:
    return _cache["categorias"]


def movimientos() -> list:
    return _cache["movimientos"]
