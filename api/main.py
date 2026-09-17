"""
Punto de entrada de la API de FerroAnalytics (Fase II).
No reemplaza main.py (menú de consola, Fase I): expone los mismos
datos y reportes de src/ por HTTP para el dashboard web.

Ejecutar con: uvicorn api.main:app --reload
"""

from dotenv import load_dotenv

load_dotenv()  # variables opcionales en .env (p. ej. FERRO_BD_URL), antes de leer nada de src/ o api/

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api import datos
from api.auth import exigir_usuario_para_mutaciones
from api.rutas import analitica, auth, inventario, reportes
from src.excepciones import (
    ArchivoCorrupto,
    DatosInsuficientes,
    ErrorAlmacenamiento,
    ErrorImportacion,
    ErrorPrediccion,
    FerroAnalyticsError,
)

ORIGENES_PERMITIDOS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    datos.cargar()
    yield


app = FastAPI(
    title="FerroAnalytics API",
    lifespan=lifespan,
    dependencies=[Depends(exigir_usuario_para_mutaciones)],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGENES_PERMITIDOS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(inventario.router)
app.include_router(reportes.router)
app.include_router(analitica.router)


# ──────────────────────────────────────────────
# Handlers de errores propios de FerroAnalytics
# ──────────────────────────────────────────────
# Cada excepción ya quedó registrada en data/logs/ al lanzarse (ver
# src/excepciones.py); aquí solo se traduce a una respuesta HTTP clara.

@app.exception_handler(ErrorImportacion)
def manejar_error_importacion(request: Request, exc: ErrorImportacion):
    return JSONResponse(status_code=400, content={"detail": exc.mensaje})


@app.exception_handler(ArchivoCorrupto)
def manejar_archivo_corrupto(request: Request, exc: ArchivoCorrupto):
    return JSONResponse(status_code=500, content={"detail": exc.mensaje})


@app.exception_handler(ErrorAlmacenamiento)
def manejar_error_almacenamiento(request: Request, exc: ErrorAlmacenamiento):
    return JSONResponse(status_code=500, content={"detail": exc.mensaje})


@app.exception_handler(DatosInsuficientes)
def manejar_datos_insuficientes(request: Request, exc: DatosInsuficientes):
    return JSONResponse(status_code=422, content={"detail": exc.mensaje})


@app.exception_handler(ErrorPrediccion)
def manejar_error_prediccion(request: Request, exc: ErrorPrediccion):
    return JSONResponse(status_code=422, content={"detail": exc.mensaje})


@app.exception_handler(FerroAnalyticsError)
def manejar_error_generico(request: Request, exc: FerroAnalyticsError):
    return JSONResponse(status_code=500, content={"detail": exc.mensaje})


@app.get("/api/salud")
def salud():
    return {"estado": "ok"}
