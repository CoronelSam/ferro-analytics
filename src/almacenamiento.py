"""
Almacenamiento binario para FerroAnalytics.
Lectura y escritura de archivos .dat usando struct.
Toda la lógica de upsert y deduplicación vive aquí.
"""

import os
import struct

from src.modelos import (
    CategoriaAnalitica,
    MovimientoAnalitico,
    ProductoAnalitico,
    FORMATO_IMPORTACION,
    TAMANO_CATEGORIA,
    TAMANO_IMPORTACION,
    TAMANO_MOVIMIENTO,
    TAMANO_PRODUCTO,
)

# ──────────────────────────────────────────────
# Rutas por defecto
# ──────────────────────────────────────────────

# La variable de entorno FERRO_BINARIOS permite trabajar con otro conjunto
# de datos (p. ej. data/binarios_historico) sin tocar los de la Fase I.
DIRECTORIO_BINARIOS = os.environ.get("FERRO_BINARIOS", os.path.join("data", "binarios"))

RUTA_PRODUCTOS     = os.path.join(DIRECTORIO_BINARIOS, "productos.dat")
RUTA_CATEGORIAS    = os.path.join(DIRECTORIO_BINARIOS, "categorias.dat")
RUTA_MOVIMIENTOS   = os.path.join(DIRECTORIO_BINARIOS, "movimientos.dat")
RUTA_IMPORTACIONES = os.path.join(DIRECTORIO_BINARIOS, "importaciones.dat")


# ──────────────────────────────────────────────
# Helpers internos
# ──────────────────────────────────────────────

def _asegurar_directorio(ruta_archivo: str) -> None:
    """Crea el directorio del archivo si no existe."""
    directorio = os.path.dirname(ruta_archivo)
    if directorio:
        os.makedirs(directorio, exist_ok=True)


def _leer_registros(ruta: str, tamano: int, deserializar) -> list:
    """
    Lee todos los registros de longitud fija de un archivo binario.

    Recibe:
        ruta        : ruta al archivo .dat.
        tamano      : bytes por registro.
        deserializar: callable que convierte bytes → objeto del modelo.

    Devuelve lista de objetos (vacía si el archivo no existe).
    """
    if not os.path.exists(ruta):
        return []
    registros = []
    with open(ruta, "rb") as f:
        while True:
            bloque = f.read(tamano)
            if len(bloque) < tamano:
                break
            registros.append(deserializar(bloque))
    return registros


def _escribir_registros(ruta: str, objetos: list, serializar) -> None:
    """
    Escribe la lista completa de objetos en un archivo binario (sobreescribe).

    Recibe:
        ruta      : ruta al archivo .dat.
        objetos   : lista de objetos del modelo.
        serializar: callable que convierte objeto → bytes.
    """
    _asegurar_directorio(ruta)
    with open(ruta, "wb") as f:
        for obj in objetos:
            f.write(serializar(obj))


def _agregar_registros(ruta: str, objetos: list, serializar) -> None:
    """
    Agrega objetos al final del archivo binario sin sobreescribir.

    Recibe:
        ruta      : ruta al archivo .dat.
        objetos   : lista de objetos a agregar.
        serializar: callable que convierte objeto → bytes.
    """
    _asegurar_directorio(ruta)
    with open(ruta, "ab") as f:
        for obj in objetos:
            f.write(serializar(obj))


# ──────────────────────────────────────────────
# Categorías
# ──────────────────────────────────────────────

def leer_categorias(ruta: str = RUTA_CATEGORIAS) -> list:
    """
    Lee todas las categorías del archivo binario.

    Devuelve lista de CategoriaAnalitica (vacía si el archivo no existe).
    """
    return _leer_registros(ruta, TAMANO_CATEGORIA, CategoriaAnalitica.desde_bytes)


def guardar_categorias(categorias: list, ruta: str = RUTA_CATEGORIAS) -> None:
    """
    Escribe la lista completa de categorías, sobreescribiendo el archivo.
    Útil para la carga inicial; si ya existen registros los reemplaza todos.

    Recibe:
        categorias: lista de CategoriaAnalitica.
    """
    _escribir_registros(ruta, categorias, lambda c: c.a_bytes())


# ──────────────────────────────────────────────
# Productos
# ──────────────────────────────────────────────

def leer_productos(ruta: str = RUTA_PRODUCTOS) -> list:
    """
    Lee todos los productos del archivo binario.

    Devuelve lista de ProductoAnalitico (vacía si el archivo no existe).
    """
    return _leer_registros(ruta, TAMANO_PRODUCTO, ProductoAnalitico.desde_bytes)


def guardar_productos(nuevos: list, ruta: str = RUTA_PRODUCTOS) -> dict:
    """
    Aplica upsert de productos sobre el archivo binario.

    Regla de negocio:
        - Si el código ya existe → actualiza stock_actual y
          fecha_ultima_actualizacion.
        - Si no existe → inserta como nuevo registro.

    Recibe:
        nuevos: lista de ProductoAnalitico provenientes del importador.

    Devuelve dict con claves 'insertados' y 'actualizados'.
    """
    existentes = {p.codigo: p for p in leer_productos(ruta)}
    insertados = 0
    actualizados = 0

    for nuevo in nuevos:
        if nuevo.codigo in existentes:
            existentes[nuevo.codigo].stock_actual = nuevo.stock_actual
            existentes[nuevo.codigo].fecha_ultima_actualizacion = nuevo.fecha_ultima_actualizacion
            actualizados += 1
        else:
            existentes[nuevo.codigo] = nuevo
            insertados += 1

    _escribir_registros(ruta, list(existentes.values()), lambda p: p.a_bytes())
    return {"insertados": insertados, "actualizados": actualizados}


def obtener_codigos_productos(ruta: str = RUTA_PRODUCTOS) -> set:
    """
    Devuelve el conjunto de códigos de producto almacenados.
    Usado por importar_movimientos para validar referencias.
    """
    return {p.codigo for p in leer_productos(ruta)}


# ──────────────────────────────────────────────
# Movimientos
# ──────────────────────────────────────────────

def leer_movimientos(ruta: str = RUTA_MOVIMIENTOS) -> list:
    """
    Lee todos los movimientos del archivo binario.

    Devuelve lista de MovimientoAnalitico (vacía si el archivo no existe).
    """
    return _leer_registros(ruta, TAMANO_MOVIMIENTO, MovimientoAnalitico.desde_bytes)


def guardar_movimientos(nuevos: list, ruta: str = RUTA_MOVIMIENTOS) -> int:
    """
    Agrega movimientos al archivo binario (sin sobreescribir los existentes).
    Los duplicados deben filtrarse antes con importar_movimientos.

    Recibe:
        nuevos: lista de MovimientoAnalitico ya validados.

    Devuelve la cantidad de registros escritos.
    """
    _agregar_registros(ruta, nuevos, lambda m: m.a_bytes())
    return len(nuevos)


def obtener_ids_movimientos(ruta: str = RUTA_MOVIMIENTOS) -> set:
    """
    Devuelve el conjunto de id_movimiento almacenados.
    Usado por importar_movimientos para detectar duplicados.
    """
    return {m.id_movimiento for m in leer_movimientos(ruta)}


# ──────────────────────────────────────────────
# Registro de importaciones
# ──────────────────────────────────────────────

def _leer_nombres_importados(ruta: str) -> list:
    """Lee todos los nombres de archivos registrados en importaciones.dat."""
    if not os.path.exists(ruta):
        return []
    nombres = []
    with open(ruta, "rb") as f:
        while True:
            bloque = f.read(TAMANO_IMPORTACION)
            if len(bloque) < TAMANO_IMPORTACION:
                break
            nombre = struct.unpack(FORMATO_IMPORTACION, bloque)[0]
            nombres.append(nombre.decode("utf-8").rstrip("\x00").strip())
    return nombres


def leer_importaciones(ruta: str = RUTA_IMPORTACIONES) -> list:
    """Devuelve los nombres de los archivos CSV ya importados, en orden de importación."""
    return _leer_nombres_importados(ruta)


def archivo_ya_importado(nombre_archivo: str, ruta: str = RUTA_IMPORTACIONES) -> bool:
    """
    Indica si el archivo CSV ya fue importado en una sesión anterior.

    Recibe:
        nombre_archivo: nombre del archivo (sin ruta), p. ej. 'productos.csv'.

    Devuelve True si ya está registrado, False en caso contrario.
    """
    return nombre_archivo in _leer_nombres_importados(ruta)


def registrar_importacion(nombre_archivo: str, ruta: str = RUTA_IMPORTACIONES) -> None:
    """
    Registra el nombre del archivo CSV como importado.

    Recibe:
        nombre_archivo: nombre del archivo (máx. 60 caracteres).
    """
    _asegurar_directorio(ruta)
    nombre_bytes = nombre_archivo.encode("utf-8").ljust(60)[:60]
    with open(ruta, "ab") as f:
        f.write(struct.pack(FORMATO_IMPORTACION, nombre_bytes))
