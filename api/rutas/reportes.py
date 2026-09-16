"""
Rutas de reportes. Cada endpoint llama directamente a la función
correspondiente de src/reportes.py sobre los datos en caché (api/datos.py).
"""

from fastapi import APIRouter, Query

from src import reportes as rep
from api import datos

router = APIRouter(prefix="/api/reportes", tags=["reportes"])


@router.get("/stock-por-categoria")
def stock_por_categoria():
    return rep.stock_por_categoria(datos.productos(), datos.categorias())


@router.get("/top-inmovilizado")
def top_inmovilizado(
    n: int = Query(default=10, ge=1),
    dias: int = Query(default=90, ge=1),
):
    return rep.top_inmovilizado(datos.productos(), datos.movimientos(), n=n, dias=dias)


@router.get("/ventas-mensuales")
def ventas_mensuales_por_categoria():
    return rep.ventas_mensuales_por_categoria(
        datos.movimientos(), datos.productos(), datos.categorias()
    )


@router.get("/alertas")
def alertas_stock_bajo(umbral: int | None = Query(default=None, ge=0)):
    return rep.alertas_stock_bajo(datos.productos(), umbral=umbral)
