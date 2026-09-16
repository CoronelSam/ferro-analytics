# Analítica de la Fase II

Metodología y fórmulas detrás de `src/clasificacion.py` y `src/prediccion.py`, y referencia de los endpoints que los exponen. Para instalación y uso general, ver el [README](../README.md).

Todos los análisis de esta página usan como fecha de referencia la del **último movimiento registrado** (`clasificacion.fecha_referencia()`), no `date.today()`: se trabaja sobre históricos que no necesariamente llegan hasta hoy.

## Clasificación ABC-XYZ (`src/clasificacion.py`)

### ABC — valor de consumo

Para cada producto, `valor_consumo = unidades_vendidas × precio_unitario_actual` (solo movimientos de salida; el precio es el actual del catálogo, no hay historial de precios). Los productos se ordenan de mayor a menor valor de consumo y se clasifican por el porcentaje acumulado:

| Clase | Corte acumulado | Interpretación |
|---|---|---|
| A | hasta 80% | Alto valor: concentra la mayor parte del consumo |
| B | 80%–95% | Valor medio |
| C | 95%–100% | Bajo valor, incluye los productos sin ventas |

### XYZ — regularidad de la demanda

Se construye la serie mensual de unidades vendidas de cada producto (0 en los meses sin ventas, dentro del período cubierto por todos los movimientos) y se calcula su coeficiente de variación, `CV = desviación estándar poblacional / media`:

| Clase | CV | Interpretación |
|---|---|---|
| X | < 0.5 | Demanda regular, fácil de pronosticar |
| Y | 0.5 – 1.0 | Demanda variable |
| Z | > 1.0 | Demanda irregular o esporádica |

Un producto sin ninguna venta tiene media 0 (CV indefinido); se reporta `cv_demanda = None` y se clasifica como `Z` (la irregularidad más alta), en vez de dividir por cero.

### Matriz combinada y recomendaciones

`clasificar_abc_xyz()` combina ambas clasificaciones en una celda de dos letras (p. ej. `AX`) con una recomendación fija:

| | X (regular) | Y (variable) | Z (irregular) |
|---|---|---|---|
| **A** | Reposición automática y frecuente, stock de seguridad bajo | Monitoreo cercano, stock de seguridad moderado | Revisión manual frecuente, evitar quiebres y sobre-stock |
| **B** | Reposición periódica estándar | Ajustar el stock de seguridad según temporada | Pedidos bajo demanda, vigilar que no se inmovilice |
| **C** | Pedidos grandes y espaciados, control mínimo | Revisión ocasional, stock mínimo | Evaluar descontinuar o vender solo bajo pedido |

`resumen_matriz()` agrupa una clasificación ya calculada por celda (cantidad de productos y valor de consumo total), para mostrarla como matriz de 3×3.

## Predicción de demanda (`src/prediccion.py`)

### Series mensuales

`serie_mensual_categoria()` y `serie_mensual_producto()` agregan unidades vendidas por mes (0 en los meses sin ventas) sobre el período cubierto por todos los movimientos (`meses_periodo()`, en `clasificacion.py`). Por producto, solo tiene sentido pronosticar los de clase **A/X** (`productos_prioritarios()`): alto valor y demanda regular, donde un modelo de series de tiempo aporta más que para un producto errático o de bajo valor.

### Los cuatro modelos

Cada modelo recibe una serie mensual sin huecos y devuelve `n` valores futuros:

| Modelo | Idea |
|---|---|
| Ingenuo | Repite el último valor observado |
| Media móvil | Repite el promedio de los últimos 3 meses |
| Suavizado exponencial simple | `nivel_t = α·real_t + (1-α)·nivel_(t-1)` (α = 0.3), repite el último nivel |
| Regresión con tendencia y estacionalidad | Regresión lineal (scikit-learn) sobre un índice temporal + 11 variables dummy de mes |

Los tres primeros son planos (repiten un solo valor para todo el horizonte); solo la regresión captura tendencia y estacionalidad. La regresión estima 1 (tendencia) + 11 (dummies de mes) + 1 (intercepto) = 13 parámetros, por lo que exige al menos **15 meses** de historial (`MINIMO_MESES_HISTORIAL`) para no degenerar en una memorización de la serie.

### Backtesting: MAE y MAPE

`backtest()` deja fuera los últimos `n_prueba` meses (3 por defecto), aplica el modelo sobre el resto y compara el pronóstico contra los valores reales de esos meses:

- **MAE** (error absoluto medio): promedio de `|real - pronóstico|`.
- **MAPE** (error porcentual absoluto medio): igual, pero como `%` sobre el valor real; los meses con demanda real 0 se excluyen (el porcentaje no está definido) y si todos lo están, `mape` es `None`.

`comparar_modelos()` evalúa los cuatro y los ordena por MAE ascendente; un modelo sin historial suficiente para evaluarse (normalmente la regresión, sobre series cortas) se omite en vez de interrumpir a los demás.

### Mínimos de datos exigidos

`pronosticar_producto()`/`pronosticar_categoria()` (los que de verdad se usan desde el menú, la API y el dashboard) exigen que la serie tenga los 15 meses de la regresión **y** que al menos 6 de esos meses tengan alguna venta; de lo contrario lanzan `DatosInsuficientes` con un mensaje que indica cuántos meses hay y cuántos tienen ventas. Es el motivo por el que los ~260 movimientos de ejemplo de la Fase I (2 a 5 por producto) no alcanzan: hace falta el histórico sintético de 24 meses (`scripts/generar_datos.py`, ver el README).

### Punto de reorden y stock de seguridad

`calcular_punto_reorden()` construye la serie **diaria** de ventas de un producto (incluye los días sin ventas dentro de su período de actividad) y aplica las fórmulas clásicas de inventario:

```
z                = NormalDist().inv_cdf(nivel_servicio)      # p. ej. 1.645 para 95%
stock_seguridad  = z × desviación_diaria × √(tiempo_entrega_días)
punto_reorden    = media_diaria × tiempo_entrega_días + stock_seguridad
```

`tiempo_entrega_dias` y `nivel_servicio` (por defecto 0.95) son parámetros: no hay un campo de tiempo de entrega en el catálogo, así que se piden en el menú, la API o el dashboard según el proveedor de cada producto.

## Referencia de la API

Todas bajo `/api/analitica`, implementadas en `api/rutas/analitica.py` sobre la caché de `api/datos.py`. Un `DatosInsuficientes` responde **422** con `{"detail": "..."}` (ver `api/main.py`); los parámetros de consulta fuera de rango responden **422** de FastAPI.

| Endpoint | Descripción | Parámetros |
|---|---|---|
| `GET /abc-xyz` | Clasificación ABC-XYZ de todos los productos | — |
| `GET /abc-xyz/resumen` | Matriz de 9 celdas (conteos y valor de consumo) | — |
| `GET /prediccion/productos-prioritarios` | Códigos de productos A/X | — |
| `GET /prediccion/categoria/{id_categoria}` | Compara los 4 modelos y pronostica una categoría | `n` (meses, 1-12), `n_prueba` (meses de backtest, 1-12) |
| `GET /prediccion/producto/{codigo}` | Igual, por producto, con punto de reorden | además `tiempo_entrega_dias` (1-90), `nivel_servicio` (0-1 exclusivo) |
