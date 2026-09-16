"""
Generador de datos históricos sintéticos para FerroAnalytics (Fase II).

Los CSV de la Fase I tienen de 2 a 5 ventas por producto en 18 meses:
no alcanzan para clasificar la demanda ni para predecirla. Este script
simula 24 meses de operación diaria (lunes a sábado) con el mismo
catálogo de data/entrada/ y escribe un conjunto coherente en
data/entrada/historico/:

    - Demanda diaria con tendencia anual y estacionalidad por categoría.
    - Productos intermitentes (compras por lote de contratistas) y
      descontinuados (dejan de venderse y quedan con stock inmovilizado).
    - Demanda real que no siempre coincide con el stock mínimo del
      catálogo (hay mínimos sobrados y otros cortos).
    - Reposición: al llegar al punto de reorden se pide para unos dos
      meses y el pedido entra tras un tiempo de entrega. Si se agota el
      stock, la venta se pierde.

El stock inicial se registra como una entrada, así que para cada producto
se cumple: suma(E) - suma(S) == stock_actual.

Uso (desde la raíz del proyecto):
    python scripts/generar_datos.py
    python scripts/generar_datos.py --cargar-en data/binarios_historico
"""

import argparse
import csv
import math
import os
import random
import sys
from datetime import date, datetime, timedelta

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from src import almacenamiento as alm  # noqa: E402
from src import importador as imp      # noqa: E402

# ──────────────────────────────────────────────
# Configuración
# ──────────────────────────────────────────────

DIRECTORIO_CATALOGO = os.path.join(RAIZ, "data", "entrada")
DIRECTORIO_SALIDA = os.path.join(RAIZ, "data", "entrada", "historico")

# Nombres distintos a los de la Fase I para que importaciones.dat no los
# confunda con categorias.csv / productos.csv / movimientos.csv.
ARCHIVO_CATEGORIAS = "categorias_historico.csv"
ARCHIVO_PRODUCTOS = "productos_historico.csv"
ARCHIVO_MOVIMIENTOS = "movimientos_historico.csv"

FECHA_INICIO = date(2024, 9, 1)
FECHA_FIN = date(2026, 8, 31)
SEMILLA = 42

DIAS_HABILES_POR_MES = 26

# Dispersión de la demanda real respecto al stock mínimo configurado.
SIGMA_POPULARIDAD = 1.1

# Factor mensual de demanda por categoría (posición 0 = enero).
ESTACIONALIDAD = {
    1: [1.00, 1.00, 1.05, 1.05, 1.00, 0.95, 0.95, 1.00, 1.00, 1.05, 1.00, 0.95],  # Tornillería
    2: [0.85, 0.90, 1.25, 1.00, 0.95, 0.95, 0.90, 0.90, 0.95, 1.00, 1.05, 1.30],  # Día del Padre (19 mar) y Navidad
    3: [0.75, 0.80, 1.35, 0.95, 0.90, 0.90, 0.85, 0.85, 0.90, 1.00, 1.15, 1.60],  # Día del Padre y Navidad
    4: [0.80, 0.85, 1.10, 1.15, 0.95, 0.85, 0.85, 0.90, 0.95, 1.05, 1.30, 1.45],  # Semana Santa y fin de año
    5: [0.90, 0.90, 0.95, 0.95, 0.95, 0.95, 0.95, 0.95, 0.95, 1.00, 1.15, 1.35],  # Instalaciones navideñas
    6: [0.85, 0.85, 0.90, 0.95, 1.10, 1.20, 1.15, 1.10, 1.15, 1.10, 0.95, 0.85],  # Temporada de lluvias
}

# Crecimiento anual de la demanda por categoría, y excepciones por producto.
TENDENCIA_CATEGORIA = {1: 0.00, 2: -0.05, 3: 0.20, 4: 0.05, 5: 0.12, 6: 0.08}
TENDENCIA_PRODUCTO = {
    "TALDR-2": 0.40,     # los inalámbricos desplazan al taladro con cable
    "TALDR-1": -0.15,
    "FOCOS-L15": 0.35,
    "FOCOS-L9": -0.10,
}

# Código → tamaño medio del lote. Se venden pocas veces, muchas unidades.
PRODUCTOS_INTERMITENTES = {
    "CABL-12": 10,
    "CABL-14": 10,
    "TUBO-2P": 20,
    "TABL-2P": 6,
    "LLAV-1P": 8,
}

# Código → fecha desde la que ya no se vende ni se repone.
PRODUCTOS_DESCONTINUADOS = {
    "SOPLA-1": date(2025, 12, 1),
    "ESMER-2": date(2026, 2, 1),
    "ESMA-NG": date(2026, 3, 1),
    "PLIE-8P": date(2026, 4, 1),
}

# Tiempo de entrega en días (mín, máx). Las eléctricas son importadas.
TIEMPO_ENTREGA = {3: (10, 20)}
TIEMPO_ENTREGA_DEFECTO = (3, 10)


# ──────────────────────────────────────────────
# Helpers de simulación
# ──────────────────────────────────────────────

def _poisson(rng: random.Random, lam: float) -> int:
    """
    Devuelve una muestra de una distribución de Poisson de media `lam`.
    Usa el algoritmo de Knuth para lam <= 30 y la aproximación normal
    para valores mayores.
    """
    if lam <= 0:
        return 0
    if lam > 30:
        return max(0, round(rng.gauss(lam, math.sqrt(lam))))
    limite = math.exp(-lam)
    k, p = 0, rng.random()
    while p > limite:
        k += 1
        p *= rng.random()
    return k


def _redondear_pedido(cantidad: int, stock_minimo: int) -> int:
    """Redondea hacia arriba al empaque habitual: 50 u. para tornillería, 5 u. para consumibles."""
    paso = 50 if stock_minimo >= 100 else 5 if stock_minimo >= 20 else 1
    return math.ceil(cantidad / paso) * paso


def _dias_habiles(inicio: date, fin: date):
    """Genera las fechas de lunes a sábado entre inicio y fin (inclusive)."""
    dia = inicio
    while dia <= fin:
        if dia.weekday() != 6:
            yield dia
        dia += timedelta(days=1)


def _simular_producto(producto, inicio: date, fin: date, rng: random.Random) -> tuple:
    """
    Simula la operación diaria de un producto.

    Recibe:
        producto: ProductoAnalitico del catálogo (usa código, categoría y mínimo).
        inicio, fin: rango de fechas a simular.
        rng: generador aleatorio con semilla.

    Devuelve:
        (movimientos, stock_final)
        movimientos: lista de tuplas (fecha, tipo, codigo, cantidad).
        stock_final: unidades en existencia al cierre de `fin`.
    """
    codigo = producto.codigo
    minimo = max(producto.stock_minimo, 1)
    estacionalidad = ESTACIONALIDAD[producto.id_categoria]
    crecimiento = TENDENCIA_PRODUCTO.get(
        codigo, TENDENCIA_CATEGORIA[producto.id_categoria] + rng.uniform(-0.05, 0.05)
    )
    # El mínimo del catálogo se fijó a ojo: la demanda real puede quedar muy
    # por encima o por debajo, y eso es lo que la Fase II debe detectar.
    popularidad = rng.lognormvariate(0, SIGMA_POPULARIDAD)
    base_diaria = minimo * 0.8 * popularidad / DIAS_HABILES_POR_MES
    lote = PRODUCTOS_INTERMITENTES.get(codigo)
    fecha_baja = PRODUCTOS_DESCONTINUADOS.get(codigo)
    entrega_min, entrega_max = TIEMPO_ENTREGA.get(producto.id_categoria, TIEMPO_ENTREGA_DEFECTO)

    # Por experiencia, el encargado pide antes de lo que marca el mínimo
    # cuando el producto se mueve rápido, y compra para unos dos meses.
    punto_reorden = max(minimo, round(base_diaria * entrega_max * 1.5))
    maximo = punto_reorden + max(2 * minimo, round(base_diaria * DIAS_HABILES_POR_MES * 2))

    stock = _redondear_pedido(round(minimo * rng.uniform(1.5, 3.0)), minimo)
    movimientos = [(inicio, "E", codigo, stock)]
    pedido = None   # (fecha_llegada, cantidad)

    for dia in _dias_habiles(inicio, fin):
        if pedido and dia >= pedido[0]:
            stock += pedido[1]
            movimientos.append((dia, "E", codigo, pedido[1]))
            pedido = None

        descontinuado = fecha_baja is not None and dia >= fecha_baja
        if descontinuado:
            continue

        anios = (dia - inicio).days / 365
        media = (base_diaria
                 * estacionalidad[dia.month - 1]
                 * (1 + crecimiento) ** anios)

        if lote:
            demanda = 0
            if rng.random() < media / lote:
                demanda = 1 + _poisson(rng, lote - 1)
        else:
            # Ruido gamma sobre la media: días flojos y días de compras grandes.
            demanda = _poisson(rng, media * rng.gammavariate(2, 0.5))

        venta = min(demanda, stock)   # sin stock, la venta se pierde
        if venta:
            stock -= venta
            movimientos.append((dia, "S", codigo, venta))

        if stock <= punto_reorden and pedido is None:
            llegada = dia + timedelta(days=rng.randint(entrega_min, entrega_max))
            if llegada.weekday() == 6:
                llegada += timedelta(days=1)
            pedido = (llegada, _redondear_pedido(maximo - stock, minimo))

    return movimientos, stock


# ──────────────────────────────────────────────
# Generación y carga
# ──────────────────────────────────────────────

def generar(inicio: date, fin: date, semilla: int, directorio: str) -> dict:
    """
    Simula todo el catálogo y escribe los tres CSV históricos.

    Recibe:
        inicio, fin: rango de fechas a simular (fin no puede ser futura).
        semilla: semilla del generador aleatorio (misma semilla → mismos datos).
        directorio: carpeta donde se escriben los CSV.

    Devuelve dict con las rutas escritas y un resumen de la simulación.
    """
    categorias, rechazadas = imp.importar_categorias(
        os.path.join(DIRECTORIO_CATALOGO, "categorias.csv"))
    productos, rechazados = imp.importar_productos(
        os.path.join(DIRECTORIO_CATALOGO, "productos.csv"))
    if rechazadas or rechazados:
        raise ValueError("El catálogo de data/entrada/ tiene filas inválidas")

    rng = random.Random(semilla)
    movimientos = []
    for producto in productos:
        movs_producto, producto.stock_actual = _simular_producto(producto, inicio, fin, rng)
        movimientos.extend(movs_producto)

    # Orden cronológico; dentro del mismo día, las entradas antes que las salidas.
    movimientos.sort(key=lambda m: (m[0], m[1] != "E", m[2]))

    os.makedirs(directorio, exist_ok=True)
    rutas = {
        "categorias": os.path.join(directorio, ARCHIVO_CATEGORIAS),
        "productos": os.path.join(directorio, ARCHIVO_PRODUCTOS),
        "movimientos": os.path.join(directorio, ARCHIVO_MOVIMIENTOS),
    }

    with open(rutas["categorias"], "w", newline="", encoding="utf-8") as f:
        escritor = csv.writer(f)
        escritor.writerow(["id", "nombre"])
        escritor.writerows([c.id, c.nombre] for c in categorias)

    with open(rutas["productos"], "w", newline="", encoding="utf-8") as f:
        escritor = csv.writer(f)
        escritor.writerow(["codigo", "nombre", "id_categoria", "precio_unitario",
                           "stock_actual", "stock_minimo"])
        escritor.writerows(
            [p.codigo, p.nombre, p.id_categoria, p.precio_unitario,
             p.stock_actual, p.stock_minimo]
            for p in productos
        )

    with open(rutas["movimientos"], "w", newline="", encoding="utf-8") as f:
        escritor = csv.writer(f)
        escritor.writerow(["id_movimiento", "codigo_producto", "tipo", "cantidad", "fecha"])
        escritor.writerows(
            [i, codigo, tipo, cantidad, fecha.isoformat()]
            for i, (fecha, tipo, codigo, cantidad) in enumerate(movimientos, start=1)
        )

    return {
        "rutas": rutas,
        "productos": len(productos),
        "movimientos": len(movimientos),
        "entradas": sum(1 for m in movimientos if m[1] == "E"),
        "salidas": sum(1 for m in movimientos if m[1] == "S"),
        "bajo_minimo": [p.codigo for p in productos if p.stock_actual < p.stock_minimo],
    }


def cargar_en_binarios(rutas_csv: dict, directorio: str) -> dict:
    """
    Importa los CSV generados a un directorio de binarios vacío, usando
    las mismas funciones de importación y almacenamiento de la Fase I.

    Recibe:
        rutas_csv: dict con las rutas 'categorias', 'productos' y 'movimientos'.
        directorio: carpeta destino de los .dat (no debe contener .dat previos).

    Devuelve dict con la cantidad de registros cargados por entidad.
    Lanza FileExistsError si el directorio ya tiene archivos .dat.
    """
    rutas_dat = {n: os.path.join(directorio, f"{n}.dat")
                 for n in ("categorias", "productos", "movimientos", "importaciones")}
    existentes = [r for r in rutas_dat.values() if os.path.exists(r)]
    if existentes:
        raise FileExistsError(
            f"'{directorio}' ya contiene binarios ({', '.join(map(os.path.basename, existentes))}); "
            "bórralos o elige otro directorio para no mezclar datos")

    categorias, _ = imp.importar_categorias(rutas_csv["categorias"])
    alm.guardar_categorias(categorias, rutas_dat["categorias"])

    productos, _ = imp.importar_productos(rutas_csv["productos"])
    alm.guardar_productos(productos, rutas_dat["productos"])

    movimientos, rechazados = imp.importar_movimientos(
        rutas_csv["movimientos"],
        alm.obtener_codigos_productos(rutas_dat["productos"]),
        alm.obtener_ids_movimientos(rutas_dat["movimientos"]),
    )
    if rechazados:
        raise ValueError(f"{len(rechazados)} movimientos rechazados; primero: {rechazados[0]}")
    alm.guardar_movimientos(movimientos, rutas_dat["movimientos"])

    for ruta in rutas_csv.values():
        alm.registrar_importacion(os.path.basename(ruta), rutas_dat["importaciones"])

    return {"categorias": len(categorias), "productos": len(productos),
            "movimientos": len(movimientos)}


def _parsear_argumentos():
    """Define y lee los argumentos de línea de comandos."""
    fecha = lambda s: datetime.strptime(s, "%Y-%m-%d").date()  # noqa: E731
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--desde", type=fecha, default=FECHA_INICIO,
                        help=f"primer día simulado (por defecto {FECHA_INICIO})")
    parser.add_argument("--hasta", type=fecha, default=FECHA_FIN,
                        help=f"último día simulado (por defecto {FECHA_FIN})")
    parser.add_argument("--semilla", type=int, default=SEMILLA,
                        help=f"semilla aleatoria (por defecto {SEMILLA})")
    parser.add_argument("--salida", default=DIRECTORIO_SALIDA,
                        help="carpeta de los CSV generados")
    parser.add_argument("--cargar-en", metavar="DIRECTORIO",
                        help="además, importa los CSV a binarios en este directorio vacío")
    args = parser.parse_args()
    if args.hasta > date.today():
        parser.error("--hasta no puede ser una fecha futura (el importador la rechazaría)")
    if args.desde >= args.hasta:
        parser.error("--desde debe ser anterior a --hasta")
    return args


def main() -> None:
    args = _parsear_argumentos()
    resumen = generar(args.desde, args.hasta, args.semilla, args.salida)

    print(f"Período simulado : {args.desde} a {args.hasta} (semilla {args.semilla})")
    print(f"Productos        : {resumen['productos']}")
    print(f"Movimientos      : {resumen['movimientos']} "
          f"({resumen['entradas']} entradas, {resumen['salidas']} salidas)")
    print(f"Bajo el mínimo   : {', '.join(resumen['bajo_minimo']) or 'ninguno'}")
    for ruta in resumen["rutas"].values():
        print(f"Escrito          : {os.path.relpath(ruta, RAIZ)}")

    if args.cargar_en:
        try:
            cargados = cargar_en_binarios(resumen["rutas"], args.cargar_en)
        except (FileExistsError, ValueError) as e:
            sys.exit(f"Error al cargar binarios: {e}")
        print(f"Binarios en {args.cargar_en}: {cargados}")


if __name__ == "__main__":
    main()
