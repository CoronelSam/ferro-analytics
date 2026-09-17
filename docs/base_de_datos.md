# Importar desde una base de datos Postgres

`src/importador_bd.py` es una alternativa a `src/importador.py` (CSV): en vez de leer un archivo, consulta directamente las tablas de categorías, productos y movimientos en una base de datos Postgres, valida cada fila con **las mismas reglas de negocio** que la versión CSV, y produce los mismos objetos del modelo (`CategoriaAnalitica`, `ProductoAnalitico`, `MovimientoAnalitico`) para guardarlos con las funciones ya existentes de `almacenamiento.py`. Todo lo que hay después de la importación (binarios, índices, clasificación, predicción, API, dashboard) no cambia.

Usa [SQLAlchemy](https://www.sqlalchemy.org) (Core, sin ORM) con el driver [psycopg 3](https://www.psycopg.org). Ambos están en `requirements.txt`.

## Configuración

La conexión se toma de la variable de entorno `FERRO_BD_URL`:

```bash
export FERRO_BD_URL="postgresql+psycopg://usuario:clave@host:5432/basededatos"
python main.py
```

No hay una forma de introducir la cadena de conexión a mano en el menú a propósito, para no fomentar escribir credenciales en la terminal o dejarlas en el historial de comandos.

## Esquema esperado

Por defecto se asume que las tablas se llaman `categorias`, `productos` y `movimientos`, con las mismas columnas que los CSV (ver el README):

```sql
CREATE TABLE categorias (
    id       INTEGER PRIMARY KEY,
    nombre   VARCHAR(30) NOT NULL
);

CREATE TABLE productos (
    codigo           VARCHAR(10) PRIMARY KEY,
    nombre           VARCHAR(40) NOT NULL,
    id_categoria     INTEGER NOT NULL,
    precio_unitario  NUMERIC(10,2) NOT NULL,
    stock_actual     INTEGER NOT NULL,
    stock_minimo     INTEGER NOT NULL
);

CREATE TABLE movimientos (
    id_movimiento     INTEGER PRIMARY KEY,
    codigo_producto   VARCHAR(10) NOT NULL,
    tipo              CHAR(1) NOT NULL,
    cantidad          INTEGER NOT NULL,
    fecha             DATE NOT NULL
);
```

Si el sistema de inventario real usa otros nombres de tabla, cada función acepta un parámetro `tabla` (por ejemplo `importar_productos_desde_bd(engine, tabla="inventario_productos")`). Los nombres de columna, en cambio, sí deben coincidir con los de arriba.

## Uso

Desde el menú de consola, opción **[8] Importar desde base de datos (Postgres)**: pide el tipo de dato (categorías, productos o movimientos), consulta la tabla correspondiente y aplica el mismo flujo de `guardar_categorias`/`guardar_productos`/`guardar_movimientos` que la importación por CSV.

Programáticamente:

```python
from src.importador_bd import crear_engine, importar_productos_desde_bd
from src import almacenamiento as alm

engine = crear_engine()  # lee FERRO_BD_URL
aceptados, rechazados = importar_productos_desde_bd(engine)
if aceptados:
    alm.guardar_productos(aceptados)
```

## Sincronización incremental de movimientos

A diferencia de categorías y productos (que siempre se leen completos y se resuelven con upsert), `movimientos.dat` es de solo agregar: releer una tabla con millones de filas en cada corrida no tiene sentido. `importar_movimientos_desde_bd` acepta `desde_id`, que agrega `WHERE id_movimiento > :desde_id` a la consulta:

```python
ids_existentes = alm.obtener_ids_movimientos()
desde_id = max(ids_existentes) if ids_existentes else None
aceptados, rechazados = importar_movimientos_desde_bd(
    engine, alm.obtener_codigos_productos(), ids_existentes, desde_id=desde_id,
)
```

Esto **asume que `id_movimiento` crece con el tiempo** en el sistema de origen (lo normal si es una columna autoincremental). Si el sistema pudiera insertar movimientos con un id menor al último ya sincronizado (por ejemplo, una corrección retroactiva), usa `desde_id=None` para traer toda la tabla y confiar solo en `ids_existentes` para deduplicar — más lento, pero no se pierde ninguna fila. El menú de consola usa `desde_id` automáticamente.

## Seguridad

Los nombres de tabla se interpolan en el SQL (SQLAlchemy no los parametriza como parametriza valores), así que `importador_bd` valida que sean un identificador simple (`^[A-Za-z_][A-Za-z0-9_]*$`) antes de construir la consulta; cualquier otro valor se rechaza con `ErrorImportacion` sin llegar a tocar la base de datos. Los valores de cada fila sí van parametrizados (`:desde_id`).
