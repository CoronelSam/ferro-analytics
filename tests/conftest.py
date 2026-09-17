"""
Configuración compartida de las pruebas de la API (pytest + TestClient).

FERRO_BINARIOS se fija a un directorio temporal ANTES de importar cualquier
módulo de src/ o api/: las rutas de los .dat y .idx (en src/almacenamiento.py
y src/indices.py) se calculan una sola vez, como valores por defecto de cada
función, en el momento en que esos módulos se importan. Importar api.main
antes de fijar la variable haría que las pruebas leyeran y escribieran los
binarios reales del proyecto (data/binarios/). FERRO_USUARIOS_DB (login,
ver api/usuarios.py) y FERRO_JWT_SECRET (api/auth.py) se aíslan igual.
"""

import glob
import os
import tempfile

import pytest

_DIR_BINARIOS = tempfile.mkdtemp(prefix="ferroanalytics_test_")
os.environ["FERRO_BINARIOS"] = _DIR_BINARIOS

_RUTA_USUARIOS = os.path.join(tempfile.mkdtemp(prefix="ferroanalytics_test_usuarios_"), "usuarios.db")
os.environ["FERRO_USUARIOS_DB"] = _RUTA_USUARIOS
os.environ["FERRO_JWT_SECRET"] = "clave-de-pruebas-no-usar-en-produccion"

from fastapi.testclient import TestClient  # noqa: E402

from api.auth import crear_token  # noqa: E402
from api.main import app  # noqa: E402
from api import usuarios as usr  # noqa: E402

USUARIO_DE_PRUEBA = "usuario_prueba"


@pytest.fixture
def cliente():
    """
    Cliente de pruebas con almacenamiento binario limpio y un usuario ya
    autenticado (header Authorization) en cada test: la mayoría de las
    pruebas no son sobre el login en sí (ver tests/api/test_auth.py), así
    que no deberían tener que lidiar con él.

    Borra los .dat/.idx del directorio temporal antes de entrar al context
    manager: al entrar se dispara el lifespan de la app (datos.cargar()),
    que recarga la caché en memoria desde ese directorio ya vacío.
    """
    for ruta in glob.glob(os.path.join(_DIR_BINARIOS, "*")):
        os.remove(ruta)
    if os.path.exists(_RUTA_USUARIOS):
        os.remove(_RUTA_USUARIOS)
    usr.crear_usuario(USUARIO_DE_PRUEBA, "Usuario de prueba", "clave-de-prueba")
    token = crear_token(USUARIO_DE_PRUEBA)
    with TestClient(app, headers={"Authorization": f"Bearer {token}"}) as client:
        yield client
