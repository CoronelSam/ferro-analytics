# FerroAnalytics

Módulo de analítica de inventario para una ferretería. No reemplaza el sistema de inventario existente: lee los CSV que este exporta, los valida, los guarda en archivos binarios propios y genera consultas, reportes y (en la Fase II) predicciones.

| Fase | Estado | Contenido |
|---|---|---|
| I | Completada | Importación de CSV, almacenamiento binario, consultas, reportes, menú de consola, pruebas en notebook |
| II | En curso | API y dashboard web, excepciones, índices binarios, clasificación ABC-XYZ, predicción de demanda |

## Requisitos

- Python 3.11 o superior
- Node.js 22 o superior y [pnpm](https://pnpm.io) (solo para el dashboard web)

## Instalación

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

La Fase I (menú de consola) solo usa la biblioteca estándar; `requirements.txt` agrega pandas, numpy, scikit-learn, matplotlib y FastAPI para la Fase II.

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
  [6] Salir
```

Para cargar los datos de ejemplo, usa la opción 1 e importa en este orden (los movimientos necesitan que los productos ya existan):

1. `data/entrada/categorias.csv`
2. `data/entrada/productos.csv`
3. `data/entrada/movimientos.csv`

Los reportes (opción 4) son: stock total por categoría, top de productos con stock inmovilizado y ventas mensuales por categoría. Los reportes y las alertas de stock bajo (opción 5) pueden exportarse a CSV en `data/reportes/`.

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

### API y dashboard web

En una terminal, la API (puerto 8000):

```bash
uvicorn api.main:app --reload
```

En otra, el dashboard (puerto 5173, redirige `/api` a la API):

```bash
pnpm --dir web run dev
```

La documentación interactiva de la API queda en http://127.0.0.1:8000/docs.

### Notebook de pruebas

`notebooks/pruebas_fase1.ipynb` documenta y ejecuta las pruebas de la Fase I: importación, consistencia del stock, no duplicación al reimportar y correctitud de los reportes. Ábrelo en VS Code o Jupyter con el kernel del `.venv`.

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

## Estructura

```
data/entrada/            CSV de ejemplo (Fase I)
data/entrada/historico/  CSV sintéticos de 24 meses (Fase II)
src/                     Lógica: modelos, importador, almacenamiento, reportes, menú
api/                     API FastAPI para el dashboard
web/                     Dashboard React + Vite
scripts/                 Generador de datos históricos
notebooks/               Pruebas y documentación en Jupyter
main.py                  Punto de entrada de la consola
```
