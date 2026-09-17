# Importar desde una base de datos (Postgres o MySQL)

`src/importador_bd.py` es una alternativa a `src/importador.py` (CSV): en vez de leer un archivo, consulta directamente las tablas de categorías, productos y movimientos en una base de datos relacional, valida cada fila con **las mismas reglas de negocio** que la versión CSV, y produce los mismos objetos del modelo (`CategoriaAnalitica`, `ProductoAnalitico`, `MovimientoAnalitico`) para guardarlos con las funciones ya existentes de `almacenamiento.py`. Todo lo que hay después de la importación (binarios, índices, clasificación, predicción, API, dashboard) no cambia.

Usa [SQLAlchemy](https://www.sqlalchemy.org) (Core, sin ORM) con SQL estándar, así que **el mismo módulo sirve para Postgres y para MySQL**: lo único que cambia es el driver instalado y el prefijo de la cadena de conexión. Ambos drivers ([psycopg 3](https://www.psycopg.org) y [PyMySQL](https://pymysql.readthedocs.io)) están en `requirements.txt`.

## Configuración

La conexión se toma de la variable de entorno `FERRO_BD_URL`. La forma más simple de definirla es un archivo `.env` en la raíz del proyecto (copia `.env.example`), que tanto `main.py` como `api/main.py` cargan automáticamente al iniciar con `python-dotenv`:

```bash
cp .env.example .env
```

```dotenv
# .env (no se versiona)
FERRO_BD_URL=postgresql+psycopg://usuario:clave@host:5432/basededatos
# o: FERRO_BD_URL=mysql+pymysql://usuario:clave@host:3306/basededatos
```

```bash
python main.py                      # o: uvicorn api.main:app --reload
```

También funciona como variable de entorno exportada a mano, si se prefiere no usar `.env`:

```bash
export FERRO_BD_URL="postgresql+psycopg://usuario:clave@host:5432/basededatos"
python main.py
```

`crear_engine()` detecta el motor por el prefijo de la URL (`engine.dialect.name`) y rechaza cualquier otro con `ErrorImportacion`; `nombre_motor(engine)` da un nombre legible ("PostgreSQL"/"MySQL") para mostrarlo, como hace el menú y el dashboard tras conectar.

No hay una forma de introducir la cadena de conexión a mano en el menú ni en el dashboard, a propósito: es la única variable de este proyecto que lleva una contraseña, y ni el menú ni el navegador son un lugar seguro para escribirla (queda en el historial de comandos, o viaja por la red desde un formulario web). `.env` cumple el mismo propósito — configurarla una sola vez — sin ese riesgo.

### MySQL: forzar `utf8mb4`

Un servidor de MySQL puede negociar `latin1` para la conexión aunque la base de datos esté creada como `utf8mb4` — es el comportamiento de fábrica en muchas instalaciones (`SHOW VARIABLES LIKE 'character_set%'` lo confirma). Sin forzar `utf8mb4` explícitamente, cualquier tilde o `ñ` se corrompe al leerla (se ve como `Ã±`, `Ã­`, etc.). Por eso `crear_engine()` agrega `?charset=utf8mb4` a la URL automáticamente cuando el motor es MySQL y la URL no trae ya un `charset` propio; Postgres no lo necesita, porque psycopg toma la codificación de la base de datos automáticamente. Si tu URL de MySQL ya especifica `charset=otro`, se respeta tal cual.

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

Este DDL es válido tanto en Postgres como en MySQL sin cambios (`NUMERIC` es un alias de `DECIMAL` en MySQL).

Si el sistema de inventario real usa otros nombres de tabla, cada función acepta un parámetro `tabla` (por ejemplo `importar_productos_desde_bd(engine, tabla="inventario_productos")`). Los nombres de columna, en cambio, sí deben coincidir con los de arriba.

## Uso

- **Menú de consola**, opción **[8] Importar desde base de datos (Postgres/MySQL)**: pide el tipo de dato (categorías, productos o movimientos), consulta la tabla correspondiente y aplica el mismo flujo de `guardar_categorias`/`guardar_productos`/`guardar_movimientos` que la importación por CSV.
- **Dashboard web**, página **Importar → pestaña "Base de datos"**: mismo flujo, con un botón "Sincronizar ahora" en vez de un formulario. `GET /api/importar-bd/estado` le dice al dashboard si hay una conexión utilizable y de qué motor, para mostrar u ocultar la sincronización en vez de fallar en cada carga cuando `FERRO_BD_URL` no está definida (el caso normal en desarrollo); `POST /api/importar-bd/{entidad}` hace la importación y devuelve el mismo `ResultadoImportacion` que ya usa la pestaña de CSV.

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

La API no tiene autenticación (igual que `/api/importar/{entidad}` con CSV), así que cualquiera que llegue al dashboard puede disparar `POST /api/importar-bd/{entidad}` y forzar una sincronización. No es un riesgo nuevo de este módulo, pero conviene tenerlo presente si el proyecto llega a exponerse fuera de una red de confianza.
