"""
Importador desde una base de datos relacional (Postgres o MySQL) para
FerroAnalytics (Fase II).

Alternativa a importador.py (CSV): lee las mismas tres tablas que el
sistema de inventario podría exponer directamente en su base de datos,
valida cada fila con las mismas reglas de negocio y devuelve los mismos
objetos del modelo, para que se guarden con las funciones ya existentes
de almacenamiento.py (guardar_categorias, guardar_productos, guardar_movimientos).

Se apoya en SQLAlchemy Core (sin ORM) con SQL estándar (SELECT simples,
parámetros nombrados), así que el mismo código sirve para ambos motores:
solo cambia el driver instalado y la cadena de conexión, que se toma de
la variable de entorno FERRO_BD_URL si no se pasa explícitamente:

    postgresql+psycopg://usuario:clave@localhost:5432/inventario   (requiere psycopg)
    mysql+pymysql://usuario:clave@localhost:3306/inventario        (requiere PyMySQL)
"""

import os
import re
from datetime import date, datetime
from typing import Tuple

from sqlalchemy import Engine, create_engine, make_url, text

from src.excepciones import ErrorImportacion
from src.importador import (
    _fila_rechazada,
    _generar_lote,
    _validar_entero_no_negativo,
    _validar_float_no_negativo,
)
from src.modelos import CategoriaAnalitica, MovimientoAnalitico, ProductoAnalitico

_NOMBRE_TABLA_VALIDO = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

_MOTORES_SOPORTADOS = {"postgresql": "PostgreSQL", "mysql": "MySQL"}


def crear_engine(url: str | None = None) -> Engine:
    """
    Crea el Engine de SQLAlchemy (Postgres o MySQL, según la URL) y prueba
    la conexión.

    Recibe:
        url: cadena de conexión SQLAlchemy; si es None, se toma de la
             variable de entorno FERRO_BD_URL. El prefijo determina el
             motor y el driver a usar: 'postgresql+psycopg://...' o
             'mysql+pymysql://...'.

    Devuelve el Engine, listo para reutilizarse en varias importaciones.

    Lanza ErrorImportacion si no hay URL disponible, el motor no es
    Postgres ni MySQL, o la conexión falla.
    """
    url = url or os.environ.get("FERRO_BD_URL")
    if not url:
        raise ErrorImportacion(
            "No se definió la conexión a la base de datos: indique 'url' o "
            "defina la variable de entorno FERRO_BD_URL, por ejemplo:\n"
            "    postgresql+psycopg://usuario:clave@host:5432/basededatos\n"
            "    mysql+pymysql://usuario:clave@host:3306/basededatos"
        )

    url_obj = make_url(url)
    # El servidor de MySQL puede negociar latin1 para la conexión aunque la
    # base de datos sea utf8mb4 (es el valor de fábrica en muchas
    # instalaciones); sin forzar utf8mb4 aquí, cualquier tilde o ñ se
    # corrompe al leerla. Postgres no tiene este problema: psycopg toma la
    # codificación de la base de datos automáticamente.
    if url_obj.get_backend_name() == "mysql" and "charset" not in url_obj.query:
        url_obj = url_obj.update_query_dict({"charset": "utf8mb4"})

    try:
        engine = create_engine(url_obj)
        with engine.connect():
            pass  # falla rápido aquí en vez de en la primera consulta
    except Exception as e:
        raise ErrorImportacion(f"No se pudo conectar a la base de datos: {e}") from e

    if engine.dialect.name not in _MOTORES_SOPORTADOS:
        raise ErrorImportacion(
            f"Motor de base de datos no soportado: '{engine.dialect.name}' "
            f"(solo Postgres y MySQL)."
        )
    return engine


def nombre_motor(engine: Engine) -> str:
    """Nombre legible del motor de un Engine ya creado (p. ej. 'PostgreSQL')."""
    return _MOTORES_SOPORTADOS.get(engine.dialect.name, engine.dialect.name)


def _validar_nombre_tabla(tabla: str) -> str:
    """
    Valida que `tabla` sea un identificador simple antes de interpolarlo en
    SQL (SQLAlchemy no parametriza nombres de tabla, solo valores).
    """
    if not _NOMBRE_TABLA_VALIDO.match(tabla):
        raise ErrorImportacion(f"Nombre de tabla inválido: '{tabla}'")
    return tabla


def _fila_a_texto(fila: dict) -> dict:
    """Convierte los valores de una fila a texto, para guardarlos en 'rechazados'."""
    return {clave: str(valor) for clave, valor in fila.items()}


def _consultar(engine: Engine, tabla: str, columnas: str, filtro: str = "", parametros: dict | None = None) -> list:
    """Ejecuta un SELECT simple y devuelve las filas como dicts."""
    tabla = _validar_nombre_tabla(tabla)
    try:
        with engine.connect() as conexion:
            resultado = conexion.execute(
                text(f"SELECT {columnas} FROM {tabla} {filtro}"), parametros or {}
            )
            return [dict(fila) for fila in resultado.mappings().all()]
    except ErrorImportacion:
        raise
    except Exception as e:
        raise ErrorImportacion(f"No se pudo leer la tabla '{tabla}': {e}") from e


def _a_fecha_iso(valor) -> str:
    """
    Normaliza un valor de fecha (date, datetime o str) a 'AAAA-MM-DD'.
    Lanza ValueError si el formato es inválido o la fecha es futura
    (misma regla que importador._parsear_fecha, adaptada a tipos nativos
    de la base de datos en vez de siempre texto).
    """
    if isinstance(valor, datetime):
        fecha = valor.date()
    elif isinstance(valor, date):
        fecha = valor
    else:
        try:
            fecha = datetime.strptime(str(valor).strip(), "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(f"Formato de fecha inválido: '{valor}' (se espera AAAA-MM-DD)")
    if fecha > date.today():
        raise ValueError(f"La fecha '{fecha.isoformat()}' es futura")
    return fecha.isoformat()


# ──────────────────────────────────────────────
# Importadores públicos
# ──────────────────────────────────────────────

def importar_categorias_desde_bd(engine: Engine, tabla: str = "categorias") -> Tuple[list, list]:
    """
    Lee la tabla de categorías y valida cada fila con las mismas reglas
    que importador.importar_categorias() (CSV).

    Recibe:
        engine: SQLAlchemy Engine (ver crear_engine()).
        tabla : nombre de la tabla, con columnas id, nombre.

    Devuelve (aceptadas, rechazadas), igual que la versión CSV.
    """
    aceptadas: list[CategoriaAnalitica] = []
    rechazadas: list[dict] = []
    filas = _consultar(engine, tabla, "id, nombre")

    for num, fila in enumerate(filas, start=1):
        try:
            id_cat = _validar_entero_no_negativo(fila["id"], "id")
            nombre = str(fila["nombre"]).strip()
            if not nombre:
                raise ValueError("'nombre' no puede estar vacío")
            aceptadas.append(CategoriaAnalitica(id=id_cat, nombre=nombre))
        except (ValueError, KeyError) as e:
            rechazadas.append(_fila_rechazada(num, _fila_a_texto(fila), str(e)))

    return aceptadas, rechazadas


def importar_productos_desde_bd(engine: Engine, tabla: str = "productos") -> Tuple[list, list]:
    """
    Lee la tabla de productos y valida cada fila con las mismas reglas
    que importador.importar_productos() (CSV).

    Recibe:
        engine: SQLAlchemy Engine (ver crear_engine()).
        tabla : nombre de la tabla, con columnas codigo, nombre,
                id_categoria, precio_unitario, stock_actual, stock_minimo.

    Devuelve (aceptados, rechazados), igual que la versión CSV.
    """
    aceptados: list[ProductoAnalitico] = []
    rechazados: list[dict] = []
    hoy = date.today().isoformat()
    filas = _consultar(
        engine, tabla,
        "codigo, nombre, id_categoria, precio_unitario, stock_actual, stock_minimo",
    )

    for num, fila in enumerate(filas, start=1):
        try:
            codigo = str(fila["codigo"]).strip()
            if not codigo:
                raise ValueError("'codigo' no puede estar vacío")
            if len(codigo) > 10:
                raise ValueError(f"'codigo' excede 10 caracteres: '{codigo}'")

            nombre = str(fila["nombre"]).strip()
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
            rechazados.append(_fila_rechazada(num, _fila_a_texto(fila), str(e)))

    return aceptados, rechazados


def importar_movimientos_desde_bd(
    engine: Engine,
    codigos_validos: set,
    ids_existentes: set,
    tabla: str = "movimientos",
    desde_id: int | None = None,
    lote: str | None = None,
) -> Tuple[list, list]:
    """
    Lee la tabla de movimientos y valida cada fila con las mismas reglas
    que importador.importar_movimientos() (CSV).

    Recibe:
        engine         : SQLAlchemy Engine (ver crear_engine()).
        codigos_validos: conjunto de códigos de producto ya almacenados.
        ids_existentes : conjunto de id_movimiento ya almacenados (para
                         detectar duplicados); se actualiza en memoria
                         durante la lectura, igual que la versión CSV.
        tabla          : nombre de la tabla, con columnas id_movimiento,
                         codigo_producto, tipo, cantidad, fecha.
        desde_id       : si se indica, solo trae filas con id_movimiento
                         mayor a este (sincronización incremental en vez
                         de traer toda la tabla en cada corrida). Asume
                         que id_movimiento crece con el tiempo en el
                         sistema de origen; si no se puede asumir eso,
                         deje este parámetro en None y confíe solo en
                         ids_existentes para deduplicar.
        lote           : identificador para etiquetar los movimientos
                         aceptados (ver importador._generar_lote); si es
                         None, se genera uno automáticamente con el motor
                         detectado. Permite deshacer esta sincronización
                         completa con almacenamiento.eliminar_movimientos_por_lote().

    Devuelve (aceptados, rechazados), igual que la versión CSV.
    """
    lote = lote or _generar_lote(f"bd-{nombre_motor(engine)}")
    aceptados: list[MovimientoAnalitico] = []
    rechazados: list[dict] = []

    filtro, parametros = "", {}
    if desde_id is not None:
        filtro, parametros = "WHERE id_movimiento > :desde_id", {"desde_id": desde_id}

    filas = _consultar(
        engine, tabla, "id_movimiento, codigo_producto, tipo, cantidad, fecha",
        filtro, parametros,
    )

    for num, fila in enumerate(filas, start=1):
        try:
            id_mov = _validar_entero_no_negativo(fila["id_movimiento"], "id_movimiento")
            if id_mov in ids_existentes:
                raise ValueError(f"id_movimiento duplicado: {id_mov}")

            codigo = str(fila["codigo_producto"]).strip()
            if not codigo:
                raise ValueError("'codigo_producto' no puede estar vacío")
            if codigo not in codigos_validos:
                raise ValueError(f"codigo_producto '{codigo}' no existe en el inventario")

            tipo = str(fila["tipo"]).strip().upper()
            if tipo not in MovimientoAnalitico.TIPOS_VALIDOS:
                raise ValueError(f"'tipo' debe ser E o S, recibido: '{tipo}'")

            cantidad = _validar_entero_no_negativo(fila["cantidad"], "cantidad")
            fecha = _a_fecha_iso(fila["fecha"])

            ids_existentes.add(id_mov)
            aceptados.append(MovimientoAnalitico(
                id_movimiento=id_mov,
                codigo_producto=codigo,
                tipo=tipo,
                cantidad=cantidad,
                fecha=fecha,
                lote_origen=lote,
            ))
        except (ValueError, KeyError) as e:
            rechazados.append(_fila_rechazada(num, _fila_a_texto(fila), str(e)))

    return aceptados, rechazados
