"""
Almacenamiento binario para FerroAnalytics.
Lectura y escritura de archivos .dat usando struct.
Toda la lógica de upsert y deduplicación vive aquí.
"""

import os
import struct

from src.excepciones import ArchivoCorrupto, ErrorAlmacenamiento
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

    Lanza ArchivoCorrupto si el tamaño del archivo no es múltiplo del
    tamaño de registro, o si algún bloque no se puede deserializar.
    """
    if not os.path.exists(ruta):
        return []

    tamano_archivo = os.path.getsize(ruta)
    if tamano_archivo % tamano != 0:
        raise ArchivoCorrupto(
            f"'{ruta}' tiene un tamaño ({tamano_archivo} bytes) que no es "
            f"múltiplo del registro ({tamano} bytes); el archivo puede estar truncado."
        )

    registros = []
    try:
        with open(ruta, "rb") as f:
            while True:
                bloque = f.read(tamano)
                if not bloque:
                    break
                registros.append(deserializar(bloque))
    except (OSError, struct.error) as e:
        raise ArchivoCorrupto(f"No se pudo leer '{ruta}': {e}") from e
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
    try:
        with open(ruta, "wb") as f:
            for obj in objetos:
                f.write(serializar(obj))
    except OSError as e:
        raise ErrorAlmacenamiento(f"No se pudo escribir '{ruta}': {e}") from e


def _agregar_registros(ruta: str, objetos: list, serializar) -> None:
    """
    Agrega objetos al final del archivo binario sin sobreescribir.

    Recibe:
        ruta      : ruta al archivo .dat.
        objetos   : lista de objetos a agregar.
        serializar: callable que convierte objeto → bytes.
    """
    _asegurar_directorio(ruta)
    try:
        with open(ruta, "ab") as f:
            for obj in objetos:
                f.write(serializar(obj))
    except OSError as e:
        raise ErrorAlmacenamiento(f"No se pudo escribir '{ruta}': {e}") from e


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
    Aplica upsert de productos sobre el archivo binario, usando productos.idx
    para ubicar los códigos existentes y actualizarlos con `seek` en vez de
    reescribir el archivo completo.

    Regla de negocio:
        - Si el código ya existe → actualiza stock_actual y
          fecha_ultima_actualizacion.
        - Si no existe → inserta como nuevo registro al final.

    Recibe:
        nuevos: lista de ProductoAnalitico provenientes del importador.

    Devuelve dict con claves 'insertados' y 'actualizados'.
    """
    from src import indices as idx

    posiciones = dict(idx.obtener_indice_productos_sincronizado(ruta))
    cambios_indice = {}
    insertados = 0
    actualizados = 0

    _asegurar_directorio(ruta)
    if not os.path.exists(ruta):
        open(ruta, "wb").close()

    try:
        with open(ruta, "r+b") as f:
            for nuevo in nuevos:
                pos = posiciones.get(nuevo.codigo)
                if pos is not None:
                    f.seek(pos)
                    existente = ProductoAnalitico.desde_bytes(f.read(TAMANO_PRODUCTO))
                    existente.stock_actual = nuevo.stock_actual
                    existente.fecha_ultima_actualizacion = nuevo.fecha_ultima_actualizacion
                    f.seek(pos)
                    f.write(existente.a_bytes())
                    actualizados += 1
                else:
                    f.seek(0, os.SEEK_END)
                    pos = f.tell()
                    f.write(nuevo.a_bytes())
                    posiciones[nuevo.codigo] = pos
                    cambios_indice[nuevo.codigo] = pos
                    insertados += 1
    except OSError as e:
        raise ErrorAlmacenamiento(f"No se pudo escribir '{ruta}': {e}") from e

    if cambios_indice:
        idx.actualizar_indice_productos(cambios_indice, ruta)

    return {"insertados": insertados, "actualizados": actualizados}


def obtener_codigos_productos(ruta: str = RUTA_PRODUCTOS) -> set:
    """
    Devuelve el conjunto de códigos de producto almacenados, leyendo
    productos.idx en vez de todo productos.dat.
    Usado por importar_movimientos para validar referencias.
    """
    from src import indices as idx

    return {codigo for codigo, _ in idx.obtener_indice_productos_sincronizado(ruta)}


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
    Agrega movimientos al archivo binario (sin sobreescribir los existentes)
    y actualiza movimientos.idx y movimientos_fecha.idx con las posiciones
    de los nuevos registros.
    Los duplicados deben filtrarse antes con importar_movimientos.

    Recibe:
        nuevos: lista de MovimientoAnalitico ya validados.

    Devuelve la cantidad de registros escritos.
    """
    from src import indices as idx

    if not nuevos:
        return 0

    # Sincroniza los índices con el estado actual del .dat antes de agregar,
    # por si no existían todavía o quedaron desactualizados.
    idx.obtener_indice_movimientos_sincronizado(ruta)
    idx.obtener_indice_movimientos_fecha_sincronizado(ruta)

    posicion = os.path.getsize(ruta) if os.path.exists(ruta) else 0
    _agregar_registros(ruta, nuevos, lambda m: m.a_bytes())

    nuevas_por_id = []
    nuevas_por_fecha = []
    for m in nuevos:
        nuevas_por_id.append((m.id_movimiento, posicion))
        nuevas_por_fecha.append((m.fecha, posicion))
        posicion += TAMANO_MOVIMIENTO

    idx.agregar_indice_movimientos(nuevas_por_id, ruta)
    idx.agregar_indice_movimientos_fecha(nuevas_por_fecha, ruta)

    return len(nuevos)


def obtener_ids_movimientos(ruta: str = RUTA_MOVIMIENTOS) -> set:
    """
    Devuelve el conjunto de id_movimiento almacenados, leyendo
    movimientos.idx en vez de todo movimientos.dat.
    Usado por importar_movimientos para detectar duplicados.
    """
    from src import indices as idx

    return {id_mov for id_mov, _ in idx.obtener_indice_movimientos_sincronizado(ruta)}


# ──────────────────────────────────────────────
# Registro de importaciones
# ──────────────────────────────────────────────

def _leer_nombres_importados(ruta: str) -> list:
    """
    Lee todos los nombres de archivos registrados en importaciones.dat.

    Lanza ArchivoCorrupto si el tamaño del archivo no es múltiplo del
    tamaño de registro.
    """
    if not os.path.exists(ruta):
        return []

    tamano_archivo = os.path.getsize(ruta)
    if tamano_archivo % TAMANO_IMPORTACION != 0:
        raise ArchivoCorrupto(
            f"'{ruta}' tiene un tamaño ({tamano_archivo} bytes) que no es "
            f"múltiplo del registro ({TAMANO_IMPORTACION} bytes); el archivo puede estar truncado."
        )

    nombres = []
    try:
        with open(ruta, "rb") as f:
            while True:
                bloque = f.read(TAMANO_IMPORTACION)
                if not bloque:
                    break
                nombre = struct.unpack(FORMATO_IMPORTACION, bloque)[0]
                nombres.append(nombre.decode("utf-8").rstrip("\x00").strip())
    except (OSError, struct.error) as e:
        raise ArchivoCorrupto(f"No se pudo leer '{ruta}': {e}") from e
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
    try:
        with open(ruta, "ab") as f:
            f.write(struct.pack(FORMATO_IMPORTACION, nombre_bytes))
    except OSError as e:
        raise ErrorAlmacenamiento(f"No se pudo registrar la importación en '{ruta}': {e}") from e
