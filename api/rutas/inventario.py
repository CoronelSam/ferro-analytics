"""
Rutas de inventario: consulta de productos, categorías, movimientos
e importación de CSV. Solo coordina entrada/salida HTTP; la lógica de
negocio vive en src/ (mismo principio que src/menu.py para la consola).
"""

import os
import tempfile

from fastapi import APIRouter, HTTPException, Query, UploadFile

from src import almacenamiento as alm
from src import importador as imp
from api import datos

router = APIRouter(prefix="/api", tags=["inventario"])

_TIPOS_ENTIDAD = {"categorias", "productos", "movimientos"}


@router.get("/productos")
def obtener_productos():
    return datos.productos()


@router.get("/categorias")
def obtener_categorias():
    return datos.categorias()


@router.get("/importaciones")
def obtener_importaciones():
    """Nombres de los archivos CSV ya importados, en orden de importación."""
    return alm.leer_importaciones()


@router.get("/movimientos")
def obtener_movimientos(
    fecha_desde: str | None = Query(default=None),
    fecha_hasta: str | None = Query(default=None),
    tipo: str | None = Query(default=None, description="E, S o None para todos"),
):
    """Filtra movimientos por rango de fechas (AAAA-MM-DD) y tipo (E/S)."""
    resultado = datos.movimientos()

    if fecha_desde:
        resultado = [m for m in resultado if m.fecha >= fecha_desde]
    if fecha_hasta:
        resultado = [m for m in resultado if m.fecha <= fecha_hasta]
    if tipo:
        tipo = tipo.upper()
        if tipo not in {"E", "S"}:
            raise HTTPException(400, "tipo debe ser 'E' o 'S'")
        resultado = [m for m in resultado if m.tipo == tipo]

    return sorted(resultado, key=lambda m: (m.fecha, m.id_movimiento))


@router.post("/importar/{entidad}")
async def importar_csv(entidad: str, archivo: UploadFile):
    """
    Importa un CSV de categorías, productos o movimientos.

    `entidad` es uno de: categorias, productos, movimientos.
    Reutiliza exactamente los importadores y reglas de deduplicación
    de src/importador.py y src/almacenamiento.py.
    """
    if entidad not in _TIPOS_ENTIDAD:
        raise HTTPException(404, f"Entidad desconocida: {entidad}")

    if alm.archivo_ya_importado(archivo.filename):
        raise HTTPException(409, f"'{archivo.filename}' ya fue importado anteriormente")

    contenido = await archivo.read()
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        tmp.write(contenido)
        ruta_temporal = tmp.name

    try:
        if entidad == "categorias":
            aceptadas, rechazadas = imp.importar_categorias(ruta_temporal)
            resultado = {"insertados": None, "actualizados": None}
            if aceptadas:
                alm.guardar_categorias(aceptadas)
        elif entidad == "productos":
            aceptadas, rechazadas = imp.importar_productos(ruta_temporal)
            resultado = {"insertados": None, "actualizados": None}
            if aceptadas:
                resultado = alm.guardar_productos(aceptadas)
        else:
            codigos = alm.obtener_codigos_productos()
            ids_existentes = alm.obtener_ids_movimientos()
            aceptadas, rechazadas = imp.importar_movimientos(ruta_temporal, codigos, ids_existentes)
            resultado = {"insertados": None, "actualizados": None}
            if aceptadas:
                alm.guardar_movimientos(aceptadas)
    except (ValueError, OSError) as e:
        raise HTTPException(400, f"Error al leer el archivo: {e}")
    finally:
        os.unlink(ruta_temporal)

    if aceptadas:
        alm.registrar_importacion(archivo.filename)
        datos.cargar()

    return {
        "entidad": entidad,
        "aceptados": len(aceptadas),
        "rechazados": rechazadas,
        **resultado,
    }
