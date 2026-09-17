"""
Usuarios del dashboard (login), en una base SQLite propia
(data/usuarios.db) separada de los .dat/.idx de productos y movimientos.
Las contraseñas se guardan hasheadas con bcrypt, nunca en texto plano.
"""

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

import bcrypt

# La variable de entorno FERRO_USUARIOS_DB permite aislar la base en las
# pruebas automatizadas (ver tests/conftest.py), igual que FERRO_BINARIOS
# en src/almacenamiento.py.
RUTA_BD_USUARIOS = os.environ.get("FERRO_USUARIOS_DB", os.path.join("data", "usuarios.db"))

# Hash de relleno para cuando el usuario no existe: sin esto,
# verificar_credenciales() respondería más rápido para un usuario
# inexistente (no hay hash contra el cual comparar) que para uno que sí
# existe pero con la contraseña incorrecta (bcrypt.checkpw corre igual),
# una diferencia de tiempo medible que permite enumerar usuarios válidos
# aunque el mensaje de error sea el mismo en los dos casos.
_HASH_DE_RELLENO = bcrypt.hashpw(b"contrasena-de-relleno", bcrypt.gensalt())


@contextmanager
def _conexion():
    directorio = os.path.dirname(RUTA_BD_USUARIOS)
    if directorio:
        os.makedirs(directorio, exist_ok=True)
    conexion = sqlite3.connect(RUTA_BD_USUARIOS)
    conexion.row_factory = sqlite3.Row
    conexion.execute(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            usuario TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            contrasena_hash TEXT NOT NULL,
            rol TEXT NOT NULL DEFAULT 'usuario',
            creado TEXT NOT NULL
        )
        """
    )
    try:
        yield conexion
        conexion.commit()
    finally:
        conexion.close()


def crear_usuario(usuario: str, nombre: str, contrasena: str, rol: str = "usuario") -> None:
    """
    Da de alta un usuario con su contraseña hasheada (bcrypt).

    Recibe el nombre de usuario (único, para iniciar sesión), el nombre
    para mostrar en el dashboard, la contraseña en texto plano y un rol
    opcional ("usuario" o "admin", sin uso todavía más allá de guardarse).

    Lanza ValueError si el usuario ya existe o la contraseña está vacía
    o supera los 72 bytes que admite bcrypt.
    """
    if len(contrasena) < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres.")
    if len(contrasena.encode("utf-8")) > 72:
        raise ValueError("La contraseña no puede superar los 72 bytes.")

    hash_contrasena = bcrypt.hashpw(contrasena.encode("utf-8"), bcrypt.gensalt()).decode("ascii")

    with _conexion() as conexion:
        existente = conexion.execute(
            "SELECT 1 FROM usuarios WHERE usuario = ?", (usuario,)
        ).fetchone()
        if existente:
            raise ValueError(f"El usuario '{usuario}' ya existe.")
        conexion.execute(
            "INSERT INTO usuarios (usuario, nombre, contrasena_hash, rol, creado) VALUES (?, ?, ?, ?, ?)",
            (usuario, nombre, hash_contrasena, rol, datetime.now(timezone.utc).isoformat()),
        )


def verificar_credenciales(usuario: str, contrasena: str) -> dict | None:
    """
    Verifica un usuario y contraseña contra la base.

    Devuelve {usuario, nombre, rol} si coinciden, o None si el usuario no
    existe o la contraseña es incorrecta.
    """
    with _conexion() as conexion:
        fila = conexion.execute(
            "SELECT usuario, nombre, contrasena_hash, rol FROM usuarios WHERE usuario = ?",
            (usuario,),
        ).fetchone()

    # bcrypt.checkpw corre siempre, exista o no el usuario (ver
    # _HASH_DE_RELLENO), para que el tiempo de respuesta no delate si el
    # usuario existe.
    hash_contrasena = fila["contrasena_hash"].encode("ascii") if fila else _HASH_DE_RELLENO
    try:
        coincide = bcrypt.checkpw(contrasena.encode("utf-8"), hash_contrasena)
    except ValueError:
        return None
    if fila is None or not coincide:
        return None
    return {"usuario": fila["usuario"], "nombre": fila["nombre"], "rol": fila["rol"]}


def obtener_usuario(usuario: str) -> dict | None:
    """Devuelve {usuario, nombre, rol} si el usuario existe, o None."""
    with _conexion() as conexion:
        fila = conexion.execute(
            "SELECT usuario, nombre, rol FROM usuarios WHERE usuario = ?", (usuario,)
        ).fetchone()
    return dict(fila) if fila else None
