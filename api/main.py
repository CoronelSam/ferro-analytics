"""
Punto de entrada de la API de FerroAnalytics (Fase II).
No reemplaza main.py (menú de consola, Fase I): expone los mismos
datos y reportes de src/ por HTTP para el dashboard web.

Ejecutar con: uvicorn api.main:app --reload
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import datos
from api.rutas import inventario, reportes

ORIGENES_PERMITIDOS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    datos.cargar()
    yield


app = FastAPI(title="FerroAnalytics API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGENES_PERMITIDOS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(inventario.router)
app.include_router(reportes.router)


@app.get("/api/salud")
def salud():
    return {"estado": "ok"}
