"""Prueba del endpoint de salud de la API."""


def test_salud_responde_ok(cliente):
    respuesta = cliente.get("/api/salud")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"estado": "ok"}
