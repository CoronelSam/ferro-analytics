"""
Rutas de inventario: consulta de productos, categorías, movimientos
e importación de CSV. Solo coordina entrada/salida HTTP; la lógica de
negocio vive en src/ (mismo principio que src/menu.py para la consola).
"""

import os
import tempfile

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile

from src import almacenamiento as alm
from src import importador as imp
from src import importador_bd as imp_bd
from src.excepciones import ErrorImportacion
from api import datos
from api.auth import exigir_admin

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
            resultado = {"insertados": None, "actualizados": None,
                         "lote": aceptadas[0].lote_origen if aceptadas else None}
            if aceptadas:
                alm.guardar_movimientos(aceptadas)
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


@router.get("/importar-bd/estado")
def estado_importar_bd():
    """
    Indica si hay una base de datos utilizable en FERRO_BD_URL, sin
    importar ninguna tabla. El dashboard la usa para mostrar u ocultar la
    sincronización, en vez de que el botón falle en cada carga cuando no
    hay ninguna base de datos configurada (el caso normal en desarrollo).
    """
    if not os.environ.get("FERRO_BD_URL"):
        return {"disponible": False, "motor": None, "detalle": None}
    try:
        engine = imp_bd.crear_engine()
    except ErrorImportacion as e:
        return {"disponible": False, "motor": None, "detalle": str(e)}
    return {"disponible": True, "motor": imp_bd.nombre_motor(engine), "detalle": None}


@router.post("/importar-bd/{entidad}")
def importar_desde_bd(entidad: str):
    """
    Importa categorías, productos o movimientos directamente desde la
    base de datos configurada en FERRO_BD_URL (Postgres o MySQL), en vez
    de subir un CSV. Reutiliza src/importador_bd.py y las mismas
    funciones de guardado que /importar/{entidad}; los movimientos se
    sincronizan de forma incremental (solo los posteriores al último
    id_movimiento ya almacenado).
    """
    if entidad not in _TIPOS_ENTIDAD:
        raise HTTPException(404, f"Entidad desconocida: {entidad}")

    engine = imp_bd.crear_engine()

    if entidad == "categorias":
        aceptadas, rechazadas = imp_bd.importar_categorias_desde_bd(engine)
        resultado = {"insertados": None, "actualizados": None}
        if aceptadas:
            alm.guardar_categorias(aceptadas)
    elif entidad == "productos":
        aceptadas, rechazadas = imp_bd.importar_productos_desde_bd(engine)
        resultado = {"insertados": None, "actualizados": None}
        if aceptadas:
            resultado = alm.guardar_productos(aceptadas)
    else:
        codigos = alm.obtener_codigos_productos()
        ids_existentes = alm.obtener_ids_movimientos()
        desde_id = max(ids_existentes) if ids_existentes else None
        aceptadas, rechazadas = imp_bd.importar_movimientos_desde_bd(
            engine, codigos, ids_existentes, desde_id=desde_id)
        resultado = {"insertados": None, "actualizados": None,
                     "lote": aceptadas[0].lote_origen if aceptadas else None}
        if aceptadas:
            alm.guardar_movimientos(aceptadas)

    if aceptadas:
        datos.cargar()

    return {
        "entidad": entidad,
        "aceptados": len(aceptadas),
        "rechazados": rechazadas,
        **resultado,
    }


@router.get("/movimientos/lotes")
def obtener_lotes_movimientos():
    """
    Lotes de movimientos identificables por lote_origen (asignado al
    importar por CSV o base de datos), para poder deshacerlos. Ver
    src/almacenamiento.py:listar_lotes_movimientos().
    """
    return alm.listar_lotes_movimientos()


@router.delete("/movimientos/lotes/{lote}")
def deshacer_lote_movimientos(lote: str, _usuario: dict = Depends(exigir_admin)):
    """
    Elimina todos los movimientos de `lote` (ver /movimientos/lotes) y
    reconstruye los índices de movimientos. Operación destructiva e
    irreversible: no afecta a categorías ni productos. Solo un usuario con
    rol "admin" puede dispararla (ver api/auth.py:exigir_admin).
    """
    eliminados = alm.eliminar_movimientos_por_lote(lote)
    if eliminados:
        datos.cargar()
    return {"lote": lote, "eliminados": eliminados}
