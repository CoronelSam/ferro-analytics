"""
Pruebas de login (api/rutas/auth.py) y de la dependency global que exige
un usuario autenticado para mutar datos (api/auth.py).

Las pruebas de login usan un TestClient propio, sin el header
Authorization que manda por defecto la fixture `cliente` (ver
tests/conftest.py): así reflejan a alguien que todavía no inició sesión,
que es el caso real que /api/auth/login tiene que resolver.
"""

from fastapi.testclient import TestClient

from api.main import app
from tests.conftest import USUARIO_DE_PRUEBA
from tests.helpers import csv_categorias


def test_login_sin_sesion_previa_devuelve_token(cliente):
    with TestClient(app) as sin_sesion:
        respuesta = sin_sesion.post(
            "/api/auth/login",
            json={"usuario": USUARIO_DE_PRUEBA, "contrasena": "clave-de-prueba"},
        )

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["usuario"] == USUARIO_DE_PRUEBA
    assert cuerpo["nombre"] == "Usuario de prueba"
    assert cuerpo["rol"] == "usuario"
    assert cuerpo["token"]


def test_login_con_contrasena_incorrecta_devuelve_401(cliente):
    with TestClient(app) as sin_sesion:
        respuesta = sin_sesion.post(
            "/api/auth/login",
            json={"usuario": USUARIO_DE_PRUEBA, "contrasena": "no-es-esta"},
        )

    assert respuesta.status_code == 401


def test_login_con_usuario_inexistente_devuelve_401(cliente):
    with TestClient(app) as sin_sesion:
        respuesta = sin_sesion.post(
            "/api/auth/login",
            json={"usuario": "no-existe", "contrasena": "lo-que-sea"},
        )

    assert respuesta.status_code == 401


def test_lectura_no_requiere_token():
    with TestClient(app) as sin_sesion:
        respuesta = sin_sesion.get("/api/productos")

    assert respuesta.status_code == 200


def test_mutacion_sin_token_devuelve_401():
    with TestClient(app) as sin_sesion:
        respuesta = sin_sesion.post(
            "/api/importar/categorias",
            files={
                "archivo": (
                    "categorias.csv",
                    csv_categorias([(1, "Herramientas")]).encode("utf-8"),
                    "text/csv",
                )
            },
        )
        assert respuesta.status_code == 401
        assert sin_sesion.get("/api/categorias").json() == []


def test_mutacion_con_token_invalido_devuelve_401(cliente):
    respuesta = cliente.post(
        "/api/importar/categorias",
        files={
            "archivo": (
                "categorias.csv",
                csv_categorias([(1, "Herramientas")]).encode("utf-8"),
                "text/csv",
            )
        },
        headers={"Authorization": "Bearer esto-no-es-un-token-valido"},
    )

    assert respuesta.status_code == 401


def test_mutacion_con_token_valido_funciona(cliente):
    respuesta = cliente.post(
        "/api/importar/categorias",
        files={
            "archivo": (
                "categorias.csv",
                csv_categorias([(1, "Herramientas")]).encode("utf-8"),
                "text/csv",
            )
        },
    )

    assert respuesta.status_code == 200
    assert cliente.get("/api/categorias").json()[0]["nombre"] == "Herramientas"
