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

### Migración de celdas mes a mes

`clasificar_abc_xyz()` mira todo el historial de una sola vez: no puede mostrar que un producto pasó, por ejemplo, de `AX` (prioridad alta, demanda estable) a `AZ` (prioridad alta, ahora impredecible) — una señal de alerta operativa más fuerte que su celda actual sola.

- `clasificacion_por_mes()` recalcula la matriz para cada mes del histórico usando una **ventana móvil** de `ventana_meses` (12 por defecto, un ciclo estacional) terminando en ese mes, en vez del historial acumulado completo. Los primeros meses del histórico quedan fuera: no alcanza ventana detrás de ellos. El precio usado sigue siendo el actual del catálogo (no hay histórico de precios).
- `migraciones()` compara cada corrida mensual contra la del mes calendario anterior y devuelve los productos cuya celda cambió: `{"mes", "codigo", "nombre", "celda_anterior", "celda_nueva"}`. Solo compara meses consecutivos (sin huecos) y nunca lanza `DatosInsuficientes`: sin historial suficiente, devuelve una lista vacía (la ausencia de migraciones también es una respuesta válida).

## Predicción de demanda (`src/prediccion.py`)

### Series mensuales

`serie_mensual_categoria()` y `serie_mensual_producto()` agregan unidades vendidas por mes (0 en los meses sin ventas) sobre el período cubierto por todos los movimientos (`meses_periodo()`, en `clasificacion.py`). Por producto, solo tiene sentido pronosticar los de clase **A/X** (`productos_prioritarios()`): alto valor y demanda regular, donde un modelo de series de tiempo aporta más que para un producto errático o de bajo valor.

### Los cinco modelos

Cada modelo recibe una serie mensual sin huecos y devuelve `n` valores futuros:

| Modelo | Idea |
|---|---|
| Ingenuo | Repite el último valor observado |
| Naive estacional | Repite el valor del mismo mes, un ciclo estacional atrás (`PERIODO_ESTACIONAL` = 12 meses) |
| Media móvil | Repite el promedio de los últimos 3 meses |
| Suavizado exponencial simple | `nivel_t = α·real_t + (1-α)·nivel_(t-1)` (α = 0.3), repite el último nivel |
| Regresión con tendencia y estacionalidad | Regresión lineal (scikit-learn) sobre un índice temporal + 11 variables dummy de mes |

Los primeros cuatro son planos (repiten uno o pocos valores para todo el horizonte); solo la regresión captura tendencia y estacionalidad explícitamente. El naive estacional es la referencia más justa para un negocio con temporadas marcadas (lluvias, fin de año de construcción): a diferencia del ingenuo simple, sí reacciona a la estacionalidad, aunque sin tendencia. Exige al menos `PERIODO_ESTACIONAL` (12) meses de historial. La regresión estima 1 (tendencia) + 11 (dummies de mes) + 1 (intercepto) = 13 parámetros, por lo que exige al menos **15 meses** de historial (`MINIMO_MESES_HISTORIAL`) para no degenerar en una memorización de la serie.

### Backtesting: MAE, MAPE y MASE

`backtest()` deja fuera los últimos `n_prueba` meses (3 por defecto), aplica el modelo sobre el resto y compara el pronóstico contra los valores reales de esos meses:

- **MAE** (error absoluto medio): promedio de `|real - pronóstico|`.
- **MAPE** (error porcentual absoluto medio): igual, pero como `%` sobre el valor real; los meses con demanda real 0 se excluyen (el porcentaje no está definido) y si todos lo están, `mape` es `None`.
- **MASE** (error absoluto medio escalado, Hyndman & Koehler 2006): el MAE del modelo sobre el período de prueba, dividido entre el MAE de un pronóstico ingenuo de un paso (`|y_t - y_(t-1)|`) calculado solo sobre el período de entrenamiento. A diferencia de MAPE no se indefine con demanda real 0 y sí es comparable entre productos con escalas muy distintas; `mase < 1` significa que el modelo supera a ese ingenuo de referencia. Es `None` si el entrenamiento es demasiado corto o constante (escala 0).

`comparar_modelos()` evalúa los cinco y los ordena por MAE ascendente (MASE conserva el mismo orden, porque divide todos los MAE de una misma serie entre la misma escala); un modelo sin historial suficiente para evaluarse (normalmente la regresión o el naive estacional, sobre series cortas) se omite en vez de interrumpir a los demás.

### Bandas de confianza del pronóstico

`pronosticar_producto()`/`pronosticar_categoria()` agregan `intervalo_confianza`: una lista `{"limite_inferior", "limite_superior"}`, una por mes pronosticado. Reutiliza el mismo criterio que `calcular_punto_reorden()` (un cuantil de la normal, `z`, por una desviación):

```
desviacion_residual = desviación estándar de (real - pronóstico) del modelo ganador sobre su propio backtest
z                    = NormalDist().inv_cdf((1 + nivel_confianza) / 2)     # p. ej. 1.96 para 95%
ancho(paso)          = z × desviacion_residual × √paso                     # paso = 1, 2, 3... meses hacia el futuro
```

El ensanche con `√paso` refleja que la incertidumbre crece cuanto más lejos se pronostica, igual que el stock de seguridad crece con `√tiempo_entrega_días`. Es una aproximación (asume errores normales e independientes con la misma desviación del backtest), no una banda estadísticamente exacta, pero alcanza para comunicar incertidumbre creciente en el dashboard sin un modelo probabilístico completo. `nivel_confianza` es un parámetro (0.95 por defecto) en `src/prediccion.py` y en la API; el menú de consola y el dashboard siempre usan ese valor por defecto, igual que ya hacían con `nivel_servicio`.

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
| `GET /abc-xyz/migraciones` | Productos cuya celda cambió respecto al mes anterior (ver arriba) | `ventana_meses` (2-36, por defecto 12) |
| `GET /prediccion/productos-prioritarios` | Códigos de productos A/X | — |
| `GET /prediccion/lote` | Pronostica todos los productos A/X de una sola vez (evita N llamadas a `/prediccion/producto/{codigo}` desde el dashboard) | mismos que `/prediccion/producto/{codigo}` |
| `GET /prediccion/categoria/{id_categoria}` | Compara los 5 modelos y pronostica una categoría, con banda de confianza | `n` (meses, 1-12), `n_prueba` (meses de backtest, 1-12), `nivel_confianza` (0-1 exclusivo) |
| `GET /prediccion/producto/{codigo}` | Igual, por producto, con punto de reorden | además `tiempo_entrega_dias` (1-90), `nivel_servicio` (0-1 exclusivo) |
