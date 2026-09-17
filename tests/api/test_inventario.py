"""
Pruebas de /api/productos, /api/categorias, /api/movimientos, importación
de CSV, lotes de movimientos y estado de importación desde base de datos.
"""

from urllib.parse import quote

from tests.helpers import csv_categorias, csv_movimientos, csv_productos, subir_csv


def test_productos_y_movimientos_vacios_al_inicio(cliente):
    assert cliente.get("/api/productos").json() == []
    assert cliente.get("/api/categorias").json() == []
    assert cliente.get("/api/movimientos").json() == []
    assert cliente.get("/api/importaciones").json() == []


def test_importar_categorias_csv_valido(cliente):
    contenido = csv_categorias([(1, "Herramientas"), (2, "Pinturas")])
    respuesta = subir_csv(cliente, "categorias", "categorias.csv", contenido)

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["entidad"] == "categorias"
    assert cuerpo["aceptados"] == 2
    assert cuerpo["rechazados"] == []

    categorias = cliente.get("/api/categorias").json()
    assert {c["nombre"] for c in categorias} == {"Herramientas", "Pinturas"}
    assert cliente.get("/api/importaciones").json() == ["categorias.csv"]


def test_importar_categorias_fila_invalida_queda_rechazada(cliente):
    contenido = "id,nombre\n1,Herramientas\nno-es-numero,Pinturas\n"
    respuesta = subir_csv(cliente, "categorias", "categorias.csv", contenido)

    cuerpo = respuesta.json()
    assert cuerpo["aceptados"] == 1
    assert len(cuerpo["rechazados"]) == 1
    assert cuerpo["rechazados"][0]["fila"] == 3
    assert "id" in cuerpo["rechazados"][0]["motivo"]


def test_importar_productos_nuevo_inserta(cliente):
    subir_csv(cliente, "categorias", "categorias.csv", csv_categorias([(1, "Herramientas")]))

    respuesta = subir_csv(
        cliente, "productos", "productos.csv",
        csv_productos([("P0001", "Martillo", 1, 250.0, 40, 5)]),
    )

    cuerpo = respuesta.json()
    assert cuerpo["aceptados"] == 1
    assert cuerpo["insertados"] == 1
    assert cuerpo["actualizados"] == 0

    productos = cliente.get("/api/productos").json()
    assert len(productos) == 1
    assert productos[0]["codigo"] == "P0001"
    assert productos[0]["stock_actual"] == 40


def test_importar_productos_existente_actualiza_stock(cliente):
    subir_csv(cliente, "categorias", "categorias.csv", csv_categorias([(1, "Herramientas")]))
    subir_csv(
        cliente, "productos", "productos_v1.csv",
        csv_productos([("P0001", "Martillo", 1, 250.0, 40, 5)]),
    )

    respuesta = subir_csv(
        cliente, "productos", "productos_v2.csv",
        csv_productos([("P0001", "Martillo", 1, 250.0, 15, 5)]),
    )

    cuerpo = respuesta.json()
    assert cuerpo["insertados"] == 0
    assert cuerpo["actualizados"] == 1

    productos = cliente.get("/api/productos").json()
    assert len(productos) == 1
    assert productos[0]["stock_actual"] == 15


def test_importar_mismo_archivo_dos_veces_devuelve_409(cliente):
    contenido = csv_categorias([(1, "Herramientas")])
    subir_csv(cliente, "categorias", "categorias.csv", contenido)

    respuesta = subir_csv(cliente, "categorias", "categorias.csv", contenido)

    assert respuesta.status_code == 409


def test_importar_entidad_desconocida_devuelve_404(cliente):
    respuesta = subir_csv(cliente, "proveedores", "x.csv", "a,b\n1,2\n")

    assert respuesta.status_code == 404


def test_importar_movimientos_requiere_producto_existente(cliente):
    subir_csv(cliente, "categorias", "categorias.csv", csv_categorias([(1, "Herramientas")]))
    subir_csv(
        cliente, "productos", "productos.csv",
        csv_productos([("P0001", "Martillo", 1, 250.0, 40, 5)]),
    )

    contenido = csv_movimientos([
        (1, "P0001", "S", 5, "2024-01-10"),
        (2, "NOEXISTE", "S", 1, "2024-01-10"),
    ])
    respuesta = subir_csv(cliente, "movimientos", "movimientos.csv", contenido)

    cuerpo = respuesta.json()
    assert cuerpo["aceptados"] == 1
    assert len(cuerpo["rechazados"]) == 1
    assert "NOEXISTE" in cuerpo["rechazados"][0]["motivo"]
    assert cuerpo["lote"] is not None


def test_movimientos_filtra_por_tipo_y_fecha(cliente):
    subir_csv(cliente, "categorias", "categorias.csv", csv_categorias([(1, "Herramientas")]))
    subir_csv(
        cliente, "productos", "productos.csv",
        csv_productos([("P0001", "Martillo", 1, 250.0, 40, 5)]),
    )
    subir_csv(cliente, "movimientos", "movimientos.csv", csv_movimientos([
        (1, "P0001", "E", 20, "2024-01-05"),
        (2, "P0001", "S", 5, "2024-02-10"),
        (3, "P0001", "S", 3, "2024-03-10"),
    ]))

    solo_salidas = cliente.get("/api/movimientos", params={"tipo": "S"}).json()
    assert {m["id_movimiento"] for m in solo_salidas} == {2, 3}

    desde_marzo = cliente.get("/api/movimientos", params={"fecha_desde": "2024-03-01"}).json()
    assert [m["id_movimiento"] for m in desde_marzo] == [3]


def test_movimientos_tipo_invalido_devuelve_400(cliente):
    respuesta = cliente.get("/api/movimientos", params={"tipo": "X"})

    assert respuesta.status_code == 400


def test_lotes_y_deshacer_lote_movimientos(cliente_admin):
    subir_csv(cliente_admin, "categorias", "categorias.csv", csv_categorias([(1, "Herramientas")]))
    subir_csv(
        cliente_admin, "productos", "productos.csv",
        csv_productos([("P0001", "Martillo", 1, 250.0, 40, 5)]),
    )
    subir_csv(cliente_admin, "movimientos", "movimientos.csv", csv_movimientos([
        (1, "P0001", "S", 5, "2024-01-10"),
        (2, "P0001", "S", 3, "2024-01-15"),
    ]))

    lotes = cliente_admin.get("/api/movimientos/lotes").json()
    assert len(lotes) == 1
    assert lotes[0]["cantidad"] == 2
    lote = lotes[0]["lote"]

    respuesta = cliente_admin.delete(f"/api/movimientos/lotes/{quote(lote, safe='')}")

    assert respuesta.status_code == 200
    assert respuesta.json()["eliminados"] == 2
    assert cliente_admin.get("/api/movimientos").json() == []
    assert cliente_admin.get("/api/movimientos/lotes").json() == []


def test_deshacer_lote_inexistente_no_elimina_nada(cliente_admin):
    respuesta = cliente_admin.delete("/api/movimientos/lotes/lote-que-no-existe")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"lote": "lote-que-no-existe", "eliminados": 0}


def test_deshacer_lote_sin_rol_admin_devuelve_403(cliente):
    """El rol por defecto ("usuario") puede importar, pero no deshacer un lote: esa acción exige rol "admin"."""
    respuesta = cliente.delete("/api/movimientos/lotes/lote-que-no-existe")

    assert respuesta.status_code == 403


def test_importar_bd_estado_sin_ferro_bd_url(cliente, monkeypatch):
    monkeypatch.delenv("FERRO_BD_URL", raising=False)

    respuesta = cliente.get("/api/importar-bd/estado")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"disponible": False, "motor": None, "detalle": None}


def test_importar_bd_entidad_desconocida_devuelve_404(cliente):
    respuesta = cliente.post("/api/importar-bd/proveedores")

    assert respuesta.status_code == 404
