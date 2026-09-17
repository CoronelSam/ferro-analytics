"""
Configuración compartida de las pruebas de la API (pytest + TestClient).

FERRO_BINARIOS se fija a un directorio temporal ANTES de importar cualquier
módulo de src/ o api/: las rutas de los .dat y .idx (en src/almacenamiento.py
y src/indices.py) se calculan una sola vez, como valores por defecto de cada
función, en el momento en que esos módulos se importan. Importar api.main
antes de fijar la variable haría que las pruebas leyeran y escribieran los
binarios reales del proyecto (data/binarios/).
"""

import glob
import os
import tempfile

import pytest

_DIR_BINARIOS = tempfile.mkdtemp(prefix="ferroanalytics_test_")
os.environ["FERRO_BINARIOS"] = _DIR_BINARIOS

from fastapi.testclient import TestClient  # noqa: E402

from api.main import app  # noqa: E402


@pytest.fixture
def cliente():
    """
    Cliente de pruebas con almacenamiento binario limpio en cada test.

    Borra los .dat/.idx del directorio temporal antes de entrar al context
    manager: al entrar se dispara el lifespan de la app (datos.cargar()),
    que recarga la caché en memoria desde ese directorio ya vacío.
    """
    for ruta in glob.glob(os.path.join(_DIR_BINARIOS, "*")):
        os.remove(ruta)
    with TestClient(app) as client:
        yield client
