"""
Autenticación por token (JWT) para las rutas que mutan datos.

Reemplaza el modo "solo lectura" de clave compartida que tenía la API
(FERRO_API_KEY) por login de usuarios (ver api/usuarios.py): cada quien
inicia sesión con su propio usuario y contraseña y recibe un token que
debe enviar en el header Authorization de cada mutación
(POST/PUT/PATCH/DELETE). Las lecturas (GET) siguen abiertas siempre.
"""

import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Header, HTTPException, Request

from api import usuarios as usr

_METODOS_DE_SOLO_LECTURA = {"GET", "HEAD", "OPTIONS"}
_RUTA_LOGIN = "/api/auth/login"
_ALGORITMO = "HS256"
_HORAS_DE_VIGENCIA = 12

# Sin FERRO_JWT_SECRET en el entorno (ver .env), se genera una al arrancar
# el proceso: los tokens dejan de ser válidos si la API se reinicia (hay
# que iniciar sesión de nuevo), pero el login funciona sin configurar nada
# extra en desarrollo. Para que las sesiones sobrevivan un reinicio real,
# definir FERRO_JWT_SECRET.
_CLAVE_SECRETA = os.environ.get("FERRO_JWT_SECRET") or secrets.token_hex(32)


def crear_token(usuario: str) -> str:
    """Genera un JWT firmado para `usuario`, válido por _HORAS_DE_VIGENCIA."""
    vencimiento = datetime.now(timezone.utc) + timedelta(hours=_HORAS_DE_VIGENCIA)
    return jwt.encode({"sub": usuario, "exp": vencimiento}, _CLAVE_SECRETA, algorithm=_ALGORITMO)


def _usuario_desde_token(token: str) -> dict:
    """
    Decodifica y valida un JWT.

    Devuelve {usuario, nombre, rol}. Lanza HTTPException 401 si el token
    es inválido, venció, o el usuario ya no existe.
    """
    try:
        payload = jwt.decode(token, _CLAVE_SECRETA, algorithms=[_ALGORITMO])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Sesión inválida o vencida. Inicia sesión de nuevo.")

    usuario = usr.obtener_usuario(payload.get("sub", ""))
    if usuario is None:
        raise HTTPException(status_code=401, detail="Sesión inválida o vencida. Inicia sesión de nuevo.")
    return usuario


async def exigir_usuario_para_mutaciones(
    request: Request, authorization: str | None = Header(default=None),
) -> None:
    """
    Dependency global (ver api/main.py): deja pasar cualquier lectura y el
    login (sin token no se puede tener un token); para el resto de
    mutaciones exige uno válido en el header `Authorization: Bearer <token>`.
    """
    if request.method in _METODOS_DE_SOLO_LECTURA or request.url.path == _RUTA_LOGIN:
        return
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Esta acción requiere iniciar sesión.",
        )
    _usuario_desde_token(authorization.removeprefix("Bearer "))
