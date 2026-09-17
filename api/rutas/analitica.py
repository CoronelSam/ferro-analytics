"""
Rutas de analítica: clasificación ABC-XYZ y predicción de demanda (Fase II).
Igual que inventario.py y reportes.py, solo coordina entrada/salida HTTP;
la lógica vive en src/clasificacion.py y src/prediccion.py. Los errores de
datos insuficientes se propagan tal cual: api/main.py ya tiene un handler
para DatosInsuficientes que responde 422 con un mensaje claro.
"""

from fastapi import APIRouter, Query

from src import clasificacion as clf
from src import prediccion as pred
from api import datos

router = APIRouter(prefix="/api/analitica", tags=["analitica"])


def _formatear_meses(pares: list) -> list:
    return [f"{anio}-{mes:02d}" for anio, mes in pares]


def _con_serie_historica(resultado: dict, meses: list, serie_historica: list) -> dict:
    return {
        **resultado,
        "meses_pronosticados": _formatear_meses(resultado["meses_pronosticados"]),
        "serie_historica": [
            {"mes": mes, "unidades": unidades}
            for mes, unidades in zip(_formatear_meses(meses), serie_historica)
        ],
    }


@router.get("/abc-xyz")
def obtener_clasificacion_abc_xyz():
    """Clasificación ABC-XYZ de todos los productos, ordenada por valor de consumo."""
    return clf.clasificar_abc_xyz(datos.productos(), datos.movimientos())


@router.get("/abc-xyz/resumen")
def obtener_resumen_abc_xyz():
    """Matriz de 9 celdas: cantidad de productos y valor de consumo por celda."""
    clasificacion = clf.clasificar_abc_xyz(datos.productos(), datos.movimientos())
    return clf.resumen_matriz(clasificacion)


@router.get("/abc-xyz/migraciones")
def obtener_migraciones_abc_xyz(
    ventana_meses: int = Query(
        default=12, ge=2, le=36,
        description="Meses trailing que entran en cada corrida mensual",
    ),
):
    """
    Productos cuya celda ABC-XYZ cambió respecto al mes calendario
    anterior (p. ej. de AX a AZ), recalculando la matriz mes a mes con una
    ventana móvil en vez de mirar todo el historial de una sola vez.
    Nunca da 422: sin historial suficiente, devuelve una lista vacía.
    """
    return clf.migraciones(datos.productos(), datos.movimientos(), ventana_meses=ventana_meses)


@router.get("/prediccion/productos-prioritarios")
def obtener_productos_prioritarios():
    """Códigos de productos A/X: los mejores candidatos para pronosticar por producto."""
    return pred.productos_prioritarios(datos.productos(), datos.movimientos())


@router.get("/prediccion/categoria/{id_categoria}")
def pronosticar_demanda_categoria(
    id_categoria: int,
    n: int = Query(default=1, ge=1, le=12, description="Meses futuros a pronosticar"),
    n_prueba: int = Query(default=3, ge=1, le=12, description="Meses finales usados para el backtest"),
    nivel_confianza: float = Query(default=0.95, gt=0, lt=1, description="Nivel de confianza del pronóstico"),
):
    """Compara los 5 modelos de pronóstico para una categoría y pronostica con el mejor."""
    productos = datos.productos()
    movimientos = datos.movimientos()
    categorias = datos.categorias()

    meses = pred.meses_periodo(movimientos)
    serie_historica = pred.serie_mensual_categoria(movimientos, productos, id_categoria, meses)
    resultado = pred.pronosticar_categoria(
        productos, movimientos, categorias, id_categoria,
        n=n, n_prueba=n_prueba, nivel_confianza=nivel_confianza,
    )
    return _con_serie_historica(resultado, meses, serie_historica)


@router.get("/prediccion/producto/{codigo}")
def pronosticar_demanda_producto(
    codigo: str,
    n: int = Query(default=1, ge=1, le=12, description="Meses futuros a pronosticar"),
    n_prueba: int = Query(default=3, ge=1, le=12, description="Meses finales usados para el backtest"),
    tiempo_entrega_dias: int = Query(default=7, ge=1, le=90),
    nivel_servicio: float = Query(default=0.95, gt=0, lt=1),
    nivel_confianza: float = Query(default=0.95, gt=0, lt=1, description="Nivel de confianza del pronóstico"),
):
    """
    Compara los 5 modelos de pronóstico para un producto, pronostica con el
    mejor y agrega su punto de reorden y stock de seguridad.
    """
    productos = datos.productos()
    movimientos = datos.movimientos()

    meses = pred.meses_periodo(movimientos)
    serie_historica = pred.serie_mensual_producto(movimientos, codigo, meses)
    resultado = pred.pronosticar_producto(
        productos, movimientos, codigo, n=n, n_prueba=n_prueba,
        tiempo_entrega_dias=tiempo_entrega_dias, nivel_servicio=nivel_servicio,
        nivel_confianza=nivel_confianza,
    )
    return _con_serie_historica(resultado, meses, serie_historica)
