"""
Pruebas de /api/analitica/* (clasificación ABC-XYZ y predicción de demanda).

src/prediccion.py exige al menos 15 meses de historial y 6 meses con ventas
(MINIMO_MESES_HISTORIAL / MINIMO_MESES_CON_DATOS) antes de pronosticar; por
debajo de eso lanza DatosInsuficientes, que la API traduce a 422. Por eso
_cargar_historial() genera 18 meses de ventas para poder probar el camino
feliz, además de los casos con datos insuficientes.
"""

from tests.helpers import csv_categorias, csv_movimientos, csv_productos, meses_hacia_atras, subir_csv

MESES_HISTORIAL = 18


def _cargar_historial(cliente):
    """
    Una categoría con dos productos y 18 meses de ventas cada uno: supera
    los mínimos de prediccion.py y da variedad de valor de consumo (para
    que la clasificación ABC no quede degenerada con un solo producto).
    """
    subir_csv(cliente, "categorias", "categorias.csv", csv_categorias([(1, "Herramientas")]))
    subir_csv(cliente, "productos", "productos.csv", csv_productos([
        ("P0001", "Martillo", 1, 100.0, 200, 20),
        ("P0002", "Clavo", 1, 100.0, 200, 20),
    ]))

    fechas = meses_hacia_atras(MESES_HISTORIAL)
    filas = []
    id_mov = 1
    for i, fecha in enumerate(fechas):
        filas.append((id_mov, "P0001", "S", 10 + (i % 3), fecha))
        id_mov += 1
        filas.append((id_mov, "P0002", "S", 30 + (i % 3), fecha))
        id_mov += 1

    subir_csv(cliente, "movimientos", "movimientos.csv", csv_movimientos(filas))
    return fechas


def test_abc_xyz_sin_datos_devuelve_422(cliente):
    respuesta = cliente.get("/api/analitica/abc-xyz")

    assert respuesta.status_code == 422
    assert "detail" in respuesta.json()


def test_abc_xyz_con_historial(cliente):
    _cargar_historial(cliente)

    clasificacion = cliente.get("/api/analitica/abc-xyz").json()

    assert {c["codigo"] for c in clasificacion} == {"P0001", "P0002"}
    for fila in clasificacion:
        assert fila["clase_abc"] in {"A", "B", "C"}
        assert fila["clase_xyz"] in {"X", "Y", "Z"}
        assert fila["celda"] == fila["clase_abc"] + fila["clase_xyz"]

    resumen = cliente.get("/api/analitica/abc-xyz/resumen").json()
    assert sum(c["num_productos"] for c in resumen) == 2


def test_migraciones_sin_datos_devuelve_lista_vacia(cliente):
    respuesta = cliente.get("/api/analitica/abc-xyz/migraciones")

    assert respuesta.status_code == 200
    assert respuesta.json() == []


def test_migraciones_con_18_meses_de_historial(cliente):
    # 18 meses alcanzan para dos corridas mensuales consecutivas con la
    # ventana por defecto (12 meses): los índices 11→12 ... 16→17 de
    # meses_hacia_atras(18), es decir 6 comparaciones mes a mes.
    _cargar_historial(cliente)

    migraciones = cliente.get("/api/analitica/abc-xyz/migraciones").json()

    for m in migraciones:
        assert set(m) == {"mes", "codigo", "nombre", "celda_anterior", "celda_nueva"}
        assert m["celda_anterior"] != m["celda_nueva"]
        assert m["codigo"] in {"P0001", "P0002"}


def test_migraciones_respeta_ventana_meses(cliente):
    _cargar_historial(cliente)

    # Con una ventana más chica que el historial disponible, debe seguir
    # respondiendo 200 (nunca 422) aunque cambie la cantidad de meses
    # comparables.
    respuesta = cliente.get("/api/analitica/abc-xyz/migraciones", params={"ventana_meses": 6})

    assert respuesta.status_code == 200
    assert isinstance(respuesta.json(), list)


def test_migraciones_ventana_fuera_de_rango_devuelve_422(cliente):
    respuesta = cliente.get("/api/analitica/abc-xyz/migraciones", params={"ventana_meses": 1})

    assert respuesta.status_code == 422


def test_productos_prioritarios_son_consistentes_con_abc_xyz(cliente):
    _cargar_historial(cliente)

    prioritarios = cliente.get("/api/analitica/prediccion/productos-prioritarios").json()
    clasificacion = {c["codigo"]: c for c in cliente.get("/api/analitica/abc-xyz").json()}

    assert set(prioritarios) <= set(clasificacion)
    assert all(clasificacion[codigo]["celda"] == "AX" for codigo in prioritarios)


def test_prediccion_producto_sin_historial_devuelve_422(cliente):
    subir_csv(cliente, "categorias", "categorias.csv", csv_categorias([(1, "Herramientas")]))
    subir_csv(
        cliente, "productos", "productos.csv",
        csv_productos([("P0001", "Martillo", 1, 100.0, 200, 20)]),
    )

    respuesta = cliente.get("/api/analitica/prediccion/producto/P0001")

    assert respuesta.status_code == 422


def test_prediccion_producto_con_historial(cliente):
    fechas = _cargar_historial(cliente)

    respuesta = cliente.get("/api/analitica/prediccion/producto/P0001", params={"n": 2})

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["codigo"] == "P0001"
    assert len(cuerpo["pronostico"]) == 2
    assert len(cuerpo["meses_pronosticados"]) == 2
    assert len(cuerpo["serie_historica"]) == len(fechas)
    assert cuerpo["mejor_modelo"] in {m["modelo"] for m in cuerpo["comparacion_modelos"]}
    assert cuerpo["punto_reorden"] >= cuerpo["stock_seguridad"] >= 0

    # Los 5 modelos (incluye naive_estacional) reportan mae/mape/mase.
    modelos = {m["modelo"] for m in cuerpo["comparacion_modelos"]}
    assert "naive_estacional" in modelos
    for m in cuerpo["comparacion_modelos"]:
        assert m["mae"] >= 0
        assert "mase" in m  # puede ser None si el entrenamiento es constante

    # Banda de confianza: un intervalo por mes pronosticado, ordenado y
    # nunca negativo (ver src/prediccion.py:_intervalos_confianza).
    assert len(cuerpo["intervalo_confianza"]) == len(cuerpo["pronostico"])
    for punto, intervalo in zip(cuerpo["pronostico"], cuerpo["intervalo_confianza"]):
        assert intervalo["limite_inferior"] <= punto <= intervalo["limite_superior"]
        assert intervalo["limite_inferior"] >= 0


def test_prediccion_producto_banda_se_ensancha_con_nivel_de_confianza(cliente):
    _cargar_historial(cliente)

    angosta = cliente.get(
        "/api/analitica/prediccion/producto/P0001", params={"nivel_confianza": 0.5},
    ).json()
    ancha = cliente.get(
        "/api/analitica/prediccion/producto/P0001", params={"nivel_confianza": 0.99},
    ).json()

    ancho_angosto = angosta["intervalo_confianza"][0]["limite_superior"] - angosta["intervalo_confianza"][0]["limite_inferior"]
    ancho_ancho = ancha["intervalo_confianza"][0]["limite_superior"] - ancha["intervalo_confianza"][0]["limite_inferior"]

    assert ancho_ancho >= ancho_angosto


def test_prediccion_categoria_con_historial(cliente):
    _cargar_historial(cliente)

    respuesta = cliente.get("/api/analitica/prediccion/categoria/1")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["id_categoria"] == 1
    assert cuerpo["nombre_categoria"] == "Herramientas"
    assert len(cuerpo["pronostico"]) == 1  # n por defecto
    assert len(cuerpo["intervalo_confianza"]) == 1


def test_prediccion_producto_codigo_inexistente_devuelve_422(cliente):
    _cargar_historial(cliente)

    respuesta = cliente.get("/api/analitica/prediccion/producto/NOEXISTE")

    assert respuesta.status_code == 422


def test_prediccion_valida_rango_de_n(cliente):
    _cargar_historial(cliente)

    respuesta = cliente.get("/api/analitica/prediccion/producto/P0001", params={"n": 13})

    assert respuesta.status_code == 422
