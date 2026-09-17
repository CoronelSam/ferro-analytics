"""
Jerarquía de excepciones propias de FerroAnalytics (Fase II) y configuración
del logging de errores en data/logs/.

Los módulos de negocio deben lanzar estas excepciones (en vez de ValueError u
OSError genéricos) cuando el error es específico del dominio: un CSV de
entrada inválido, un archivo binario corrupto o datos insuficientes para
predecir. Así la consola y la API pueden distinguir el tipo de error y
mostrar un mensaje claro en vez de un traceback.
"""

import logging
import os

DIRECTORIO_LOGS = os.path.join("data", "logs")
RUTA_LOG = os.path.join(DIRECTORIO_LOGS, "ferroanalytics.log")


def configurar_logging(nivel: int = logging.INFO) -> logging.Logger:
    """
    Configura el logger 'ferroanalytics' para escribir en data/logs/ferroanalytics.log.
    Es seguro llamarla varias veces: no duplica handlers.

    Devuelve el logger configurado.
    """
    logger = logging.getLogger("ferroanalytics")
    if logger.handlers:
        return logger

    os.makedirs(DIRECTORIO_LOGS, exist_ok=True)
    manejador = logging.FileHandler(RUTA_LOG, encoding="utf-8")
    manejador.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)-8s %(name)s: %(message)s"
    ))
    logger.addHandler(manejador)
    logger.setLevel(nivel)
    logger.propagate = False
    return logger


_logger = configurar_logging()


class FerroAnalyticsError(Exception):
    """
    Base de todas las excepciones propias de FerroAnalytics.
    Registra automáticamente un mensaje de error en data/logs/ al crearse.
    """

    def __init__(self, mensaje: str):
        super().__init__(mensaje)
        self.mensaje = mensaje
        _logger.error("%s: %s", type(self).__name__, mensaje)


class ErrorImportacion(FerroAnalyticsError):
    """Error al leer datos de entrada, sea un CSV (columnas faltantes, archivo ilegible) o una base de datos externa (conexión, tabla inexistente)."""


class ErrorAlmacenamiento(FerroAnalyticsError):
    """Error al leer o escribir un archivo binario (.dat)."""


class ArchivoCorrupto(ErrorAlmacenamiento):
    """El archivo binario existe pero su contenido no es válido (tamaño no múltiplo del registro, bytes ilegibles)."""


class ErrorPrediccion(FerroAnalyticsError):
    """Error al calcular una clasificación o predicción de demanda."""


class DatosInsuficientes(ErrorPrediccion):
    """No hay suficiente historial de movimientos para generar una predicción confiable."""
