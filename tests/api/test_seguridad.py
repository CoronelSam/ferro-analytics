"""
Pruebas del modo solo lectura opcional (api/seguridad.py, FERRO_API_KEY).

api/main.py aplica exigir_clave_para_mutaciones como dependency global; la
clave se lee del entorno en cada request (no al importar el módulo), así
que monkeypatch.setenv/delenv dentro de cada test alcanza sin necesidad de
recargar nada.
"""

from tests.helpers import csv_categorias, subir_csv


def test_salud_reporta_solo_lectura_desactivado_por_defecto(cliente, monkeypatch):
    monkeypatch.delenv("FERRO_API_KEY", raising=False)

    respuesta = cliente.get("/api/salud")

    assert respuesta.json() == {"estado": "ok", "solo_lectura": False}


def test_salud_reporta_solo_lectura_activado(cliente, monkeypatch):
    monkeypatch.setenv("FERRO_API_KEY", "clave-secreta")

    respuesta = cliente.get("/api/salud")

    assert respuesta.json() == {"estado": "ok", "solo_lectura": True}


def test_get_no_requiere_clave_aunque_este_configurada(cliente, monkeypatch):
    monkeypatch.setenv("FERRO_API_KEY", "clave-secreta")

    respuesta = cliente.get("/api/productos")

    assert respuesta.status_code == 200


def test_mutacion_funciona_sin_clave_configurada(cliente, monkeypatch):
    monkeypatch.delenv("FERRO_API_KEY", raising=False)

    respuesta = subir_csv(cliente, "categorias", "categorias.csv", csv_categorias([(1, "Herramientas")]))

    assert respuesta.status_code == 200


def test_mutacion_sin_header_devuelve_403_con_clave_configurada(cliente, monkeypatch):
    monkeypatch.setenv("FERRO_API_KEY", "clave-secreta")

    respuesta = subir_csv(cliente, "categorias", "categorias.csv", csv_categorias([(1, "Herramientas")]))

    assert respuesta.status_code == 403
    assert "X-API-Key" in respuesta.json()["detail"]
    assert cliente.get("/api/categorias").json() == []  # la mutación no se aplicó


def test_mutacion_con_clave_incorrecta_devuelve_403(cliente, monkeypatch):
    monkeypatch.setenv("FERRO_API_KEY", "clave-secreta")

    respuesta = cliente.post(
        "/api/importar/categorias",
        files={"archivo": ("categorias.csv", csv_categorias([(1, "Herramientas")]).encode("utf-8"), "text/csv")},
        headers={"X-API-Key": "clave-incorrecta"},
    )

    assert respuesta.status_code == 403


def test_mutacion_con_clave_correcta_funciona(cliente, monkeypatch):
    monkeypatch.setenv("FERRO_API_KEY", "clave-secreta")

    respuesta = cliente.post(
        "/api/importar/categorias",
        files={"archivo": ("categorias.csv", csv_categorias([(1, "Herramientas")]).encode("utf-8"), "text/csv")},
        headers={"X-API-Key": "clave-secreta"},
    )

    assert respuesta.status_code == 200
    assert cliente.get("/api/categorias").json()[0]["nombre"] == "Herramientas"


def test_deshacer_lote_bloqueado_sin_clave(cliente, monkeypatch):
    monkeypatch.setenv("FERRO_API_KEY", "clave-secreta")

    respuesta = cliente.delete("/api/movimientos/lotes/algun-lote")

    assert respuesta.status_code == 403
