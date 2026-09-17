"""Pruebas de /api/reportes/* sobre datos importados directamente vía CSV."""

from datetime import date

from tests.helpers import csv_categorias, csv_movimientos, csv_productos, subir_csv


def _cargar_datos_basicos(cliente):
    subir_csv(cliente, "categorias", "categorias.csv", csv_categorias([
        (1, "Herramientas"), (2, "Pinturas"),
    ]))
    subir_csv(cliente, "productos", "productos.csv", csv_productos([
        ("P0001", "Martillo", 1, 100.0, 10, 5),
        ("P0002", "Destornillador", 1, 50.0, 2, 5),
        ("P0003", "Pintura Blanca", 2, 20.0, 30, 10),
    ]))


def test_stock_por_categoria(cliente):
    _cargar_datos_basicos(cliente)

    reporte = cliente.get("/api/reportes/stock-por-categoria").json()
    por_id = {r["id_categoria"]: r for r in reporte}

    assert por_id[1]["num_productos"] == 2
    assert por_id[1]["stock_total"] == 12
    assert por_id[1]["valor_total"] == 10 * 100.0 + 2 * 50.0

    assert por_id[2]["num_productos"] == 1
    assert por_id[2]["stock_total"] == 30
    assert por_id[2]["valor_total"] == 30 * 20.0


def test_alertas_stock_bajo_usa_stock_minimo_por_defecto(cliente):
    _cargar_datos_basicos(cliente)

    alertas = cliente.get("/api/reportes/alertas").json()

    assert {a["codigo"] for a in alertas} == {"P0002"}  # stock_actual=2 < stock_minimo=5


def test_alertas_stock_bajo_respeta_umbral_explicito(cliente):
    _cargar_datos_basicos(cliente)

    alertas = cliente.get("/api/reportes/alertas", params={"umbral": 15}).json()

    assert {a["codigo"] for a in alertas} == {"P0001", "P0002"}  # ambos < 15


def test_top_inmovilizado_respeta_parametro_n(cliente):
    _cargar_datos_basicos(cliente)

    # Sin movimientos de salida, los 3 productos están inmovilizados; el
    # reporte debe traer los `n` de mayor valor inmovilizado, descendente.
    reporte = cliente.get("/api/reportes/top-inmovilizado", params={"n": 2}).json()

    assert [p["codigo"] for p in reporte] == ["P0001", "P0003"]


def test_top_inmovilizado_excluye_con_salida_reciente(cliente):
    _cargar_datos_basicos(cliente)
    subir_csv(cliente, "movimientos", "movimientos.csv", csv_movimientos([
        (1, "P0001", "S", 1, date.today().isoformat()),
    ]))

    reporte = cliente.get("/api/reportes/top-inmovilizado").json()
    codigos = {p["codigo"] for p in reporte}

    assert "P0001" not in codigos
    assert {"P0002", "P0003"} <= codigos


def test_ventas_mensuales_por_categoria(cliente):
    _cargar_datos_basicos(cliente)
    subir_csv(cliente, "movimientos", "movimientos.csv", csv_movimientos([
        (1, "P0001", "S", 4, "2024-01-15"),
        (2, "P0002", "S", 2, "2024-01-20"),
        (3, "P0003", "S", 6, "2024-02-05"),
        (4, "P0001", "E", 100, "2024-01-10"),  # entrada: no cuenta como venta
    ]))

    reporte = cliente.get("/api/reportes/ventas-mensuales").json()
    por_clave = {(r["anio"], r["mes"], r["id_categoria"]): r["unidades"] for r in reporte}

    assert por_clave[(2024, 1, 1)] == 6  # P0001 + P0002, categoría 1
    assert por_clave[(2024, 2, 2)] == 6  # P0003, categoría 2
