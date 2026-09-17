# FerroAnalytics

Módulo de analítica de inventario para una ferretería. No reemplaza el sistema de inventario existente: lee los CSV que este exporta, los valida, los guarda en archivos binarios propios y genera consultas, reportes y (en la Fase II) predicciones.

| Fase | Estado | Contenido |
|---|---|---|
| I | Completada | Importación de CSV, almacenamiento binario, consultas, reportes, menú de consola, pruebas en notebook |
| II | Completada | Excepciones propias y logging, índices binarios, clasificación ABC-XYZ, predicción de demanda, API y dashboard web |

## Requisitos

- Python 3.11 o superior
- Node.js 22 o superior y [pnpm](https://pnpm.io) (solo para el dashboard web)

## Instalación

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

La Fase I (menú de consola) solo usa la biblioteca estándar; `requirements.txt` agrega pandas, numpy, scikit-learn, matplotlib, SQLAlchemy + psycopg/PyMySQL y FastAPI para la Fase II.

Para el dashboard:

```bash
pnpm --dir web install
```

## Uso

### Menú de consola

```bash
python main.py
```

```
════════════════════════════════════════════════════════════
  FerroAnalytics – Menú Principal
════════════════════════════════════════════════════════════
  [1] Importar datos (CSV)
  [2] Consultar inventario actual
  [3] Consultar movimientos por período
  [4] Ver reportes
  [5] Ver alertas de stock bajo
  [6] Clasificación ABC-XYZ
  [7] Predicción de demanda
  [8] Importar desde base de datos (Postgres/MySQL)
  [9] Deshacer una importación de movimientos
  [10] Salir
```

Para cargar los datos de ejemplo, usa la opción 1 e importa en este orden (los movimientos necesitan que los productos ya existan):

1. `data/entrada/categorias.csv`
2. `data/entrada/productos.csv`
3. `data/entrada/movimientos.csv`

Los reportes (opción 4) son: stock total por categoría, top de productos con stock inmovilizado y ventas mensuales por categoría. Los reportes y las alertas de stock bajo (opción 5) pueden exportarse a CSV en `data/reportes/`. Las opciones 6 y 7 son de la Fase II (ver [Analítica](#analítica-fase-ii) más abajo) y necesitan más historial que los datos de ejemplo: usa el histórico sintético. La opción 8 importa directamente desde Postgres o MySQL en vez de un CSV, y la 9 deshace una importación de movimientos por lote (ver [Base de datos](#importar-desde-una-base-de-datos-postgres-o-mysql) más abajo).

### Datos históricos (Fase II)

Los datos de ejemplo de la Fase I tienen muy pocas ventas por producto para clasificar o predecir la demanda. `scripts/generar_datos.py` simula 24 meses de operación con el mismo catálogo (tendencia, estacionalidad, productos intermitentes y descontinuados) y escribe los CSV en `data/entrada/historico/`. Con `--cargar-en` también los importa a binarios:

```bash
python scripts/generar_datos.py --cargar-en data/binarios_historico
```

El directorio destino debe estar vacío, para no mezclar datos. La misma semilla (`--semilla`, por defecto 42) produce siempre los mismos datos.

Para que el menú o la API usen ese conjunto en lugar de `data/binarios`, define `FERRO_BINARIOS`:

```bash
FERRO_BINARIOS=data/binarios_historico python main.py
```

### Importar desde una base de datos Postgres o MySQL

Además del CSV, `src/importador_bd.py` puede leer categorías, productos y movimientos directamente de una base de datos Postgres o MySQL (vía SQLAlchemy, con psycopg o PyMySQL según el motor), con las mismas reglas de validación y las mismas funciones de `almacenamiento.py` para guardarlos. Se configura con la variable de entorno `FERRO_BD_URL`, nunca escribiendo la conexión en el menú ni en el dashboard; lo más simple es copiar `.env.example` a `.env` (`main.py` y `api/main.py` lo cargan solos al iniciar):

```bash
cp .env.example .env   # y completa FERRO_BD_URL ahí
python main.py         # opción [8] · o: uvicorn api.main:app --reload, pestaña "Base de datos" del dashboard
```

Cada importación de movimientos (CSV o base de datos) queda etiquetada con un lote; la opción **[9]** del menú y la pestaña **Importar → Deshacer** del dashboard permiten eliminar solo los movimientos de un lote (no afecta a categorías ni productos), con confirmación explícita antes de borrar.

Detalles del esquema esperado, cómo apuntar a otros nombres de tabla, la sincronización incremental de movimientos, cómo deshacer una importación por lote y un problema de codificación de MySQL que `crear_engine()` corrige solo, están en [`docs/base_de_datos.md`](docs/base_de_datos.md).

### Analítica (Fase II)

Además de los reportes descriptivos de la Fase I, `src/clasificacion.py` y `src/prediccion.py` agregan:

- **Clasificación ABC-XYZ**: ABC por valor de consumo (unidades vendidas × precio actual, cortes en 80%/95% acumulado) y XYZ por el coeficiente de variación de la demanda mensual, combinados en una matriz de 9 celdas con una recomendación de manejo para cada una.
- **Predicción de demanda**: series mensuales por categoría o por producto (solo los de clase A/X: alto valor y demanda estable), comparando cuatro modelos por *backtesting* (MAE/MAPE) — ingenuo, media móvil, suavizado exponencial y una regresión con tendencia + estacionalidad — y el punto de reorden / stock de seguridad de un producto según su demanda diaria observada.

Ambas necesitan más historial del que trae `data/entrada/` (ver [Datos históricos](#datos-históricos-fase-ii) arriba); con la muestra de la Fase I, predecir por producto normalmente lanza un error de datos insuficientes en vez de dar un resultado poco confiable. El detalle de las fórmulas y los mínimos de datos exigidos está en [`docs/analitica.md`](docs/analitica.md).

Disponibles en el menú de consola (opciones 6 y 7), en el dashboard (pestaña **Analítica**) y por API en `/api/analitica/*`.

### API y dashboard web

En una terminal, la API (puerto 8000):

```bash
uvicorn api.main:app --reload
```

En otra, el dashboard (puerto 5173, redirige `/api` a la API):

```bash
pnpm --dir web run dev
```

La documentación interactiva de la API queda en http://127.0.0.1:8000/docs. Los errores propios de FerroAnalytics (CSV inválido, binario corrupto, datos insuficientes para predecir) responden con el código HTTP correspondiente y `{"detail": "..."}`, y además quedan registrados en `data/logs/ferroanalytics.log`.

### Notebooks de pruebas

- `notebooks/pruebas_fase1.ipynb`: importación, consistencia del stock, no duplicación al reimportar y correctitud de los reportes (Fase I).
- `notebooks/pruebas_fase2.ipynb`: jerarquía de excepciones y logging, índices binarios (búsqueda, upsert con `seek`, reconstrucción), clasificación ABC-XYZ y predicción de demanda, sobre el histórico sintético.

Ábrelos en VS Code o Jupyter con el kernel del `.venv`.

### Pruebas de la API (pytest)

```bash
pytest
```

`tests/` usa `fastapi.testclient.TestClient` contra `api/main.py`: cada prueba corre con `FERRO_BINARIOS` apuntando a un directorio temporal propio (ver `tests/conftest.py`), así que nunca toca `data/binarios/` ni el histórico. Cubre importación de CSV (alta, upsert, duplicados, filas rechazadas), consulta y filtrado de movimientos, lotes y su reversión, los cuatro reportes, y clasificación/predicción de la Fase II (incluyendo el 422 de `DatosInsuficientes` cuando no hay historial suficiente).

## Formato de los CSV de entrada

Codificación UTF-8, con encabezado en la primera fila. Las fechas usan el formato `AAAA-MM-DD`.

**categorias.csv**

```
id,nombre
1,Tornillería
```

**productos.csv**

```
codigo,nombre,id_categoria,precio_unitario,stock_actual,stock_minimo
TORN-M4,Tornillo M4 x 20mm zinc,1,0.08,2000,500
```

**movimientos.csv**

```
id_movimiento,codigo_producto,tipo,cantidad,fecha
1,DEST-PL6,E,55,2025-01-05
```

`tipo` es `E` (entrada) o `S` (salida).

### Reglas de validación

- `codigo` tiene como máximo 10 caracteres; `nombre` se recorta a 40 (productos) o 30 (categorías).
- Cantidades, precios y stock deben ser números no negativos.
- Las fechas deben ser válidas y no futuras.
- Un movimiento se rechaza si su `codigo_producto` no existe o si su `id_movimiento` ya está almacenado.
- Si el código de un producto ya existe, se actualizan `stock_actual` y la fecha de última actualización; si no, se inserta.
- Las filas inválidas no detienen la importación: se listan al final con su número de fila y el motivo.
- Cada archivo importado queda registrado por nombre; si se intenta importar de nuevo, el menú pide confirmación y la API lo rechaza.

## Almacenamiento binario

Registros de longitud fija empaquetados con `struct` (little-endian), en `data/binarios/`:

| Archivo | Registro | Formato |
|---|---|---|
| `productos.dat` | código, nombre, id_categoria, precio, stock_actual, stock_minimo, fecha_actualización | `<10s40sifii10s` |
| `categorias.dat` | id, nombre | `<i30s` |
| `movimientos.dat` | id, código_producto, tipo, cantidad, fecha, lote_origen | `<i10s1si10s40s` |
| `importaciones.dat` | nombre del CSV importado | `60s` |

Los binarios no se versionan: se regeneran importando los CSV.

### Índices binarios (Fase II)

`src/indices.py` mantiene, junto a cada `.dat`, un índice ordenado que mapea clave → posición:

| Archivo | Clave → posición | Formato |
|---|---|---|
| `productos.idx` | código → offset en `productos.dat` | `<10si` |
| `movimientos.idx` | id_movimiento → offset en `movimientos.dat` | `<ii` |
| `movimientos_fecha.idx` | fecha → offset en `movimientos.dat` (clave repetible) | `<10si` |

Permiten ubicar un registro con búsqueda binaria (sin leer todo el `.dat`) y, en `guardar_productos`, actualizar un producto existente con `seek` en vez de reescribir el archivo completo. Si un `.idx` falta, está corrupto o desincronizado con su `.dat`, se reconstruye solo; también puede forzarse con `src.indices.reconstruir_indices()`.

## Excepciones y logging (Fase II)

`src/excepciones.py` define `FerroAnalyticsError` como base de `ErrorImportacion`, `ErrorAlmacenamiento` (con `ArchivoCorrupto`) y `ErrorPrediccion` (con `DatosInsuficientes`). Se usan en vez de `ValueError`/`OSError` genéricos para que el menú y la API puedan mostrar un mensaje claro; cada una se registra automáticamente en `data/logs/ferroanalytics.log` al crearse.

## Estructura

```
data/entrada/            CSV de ejemplo (Fase I)
data/entrada/historico/  CSV sintéticos de 24 meses (Fase II)
data/logs/               Log de errores (Fase II, no versionado)
docs/                    Documentación de la Fase II (analítica, base de datos)
src/                     modelos, importador, almacenamiento, reportes, menú (Fase I)
                         excepciones, indices, clasificacion, prediccion, importador_bd (Fase II)
api/                     API FastAPI para el dashboard, incluye /api/analitica/*
web/                     Dashboard React + Vite, incluye la pestaña Analítica
scripts/                 Generador de datos históricos
notebooks/               Pruebas y documentación en Jupyter (Fase I y Fase II)
main.py                  Punto de entrada de la consola
```
