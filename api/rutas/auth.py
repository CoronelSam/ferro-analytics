"""
Ruta de autenticación: login de usuarios del dashboard (ver
api/usuarios.py, api/auth.py). Solo coordina entrada/salida HTTP.
"""

from fastapi import APIRouter, HTTPException

from api import usuarios as usr
from api.auth import crear_token
from api.esquemas import SesionUsuario, SolicitudLogin

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=SesionUsuario)
def iniciar_sesion(solicitud: SolicitudLogin):
    usuario = usr.verificar_credenciales(solicitud.usuario, solicitud.contrasena)
    if usuario is None:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos.")
    token = crear_token(usuario["usuario"])
    return SesionUsuario(token=token, **usuario)
