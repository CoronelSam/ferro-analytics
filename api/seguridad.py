"""
Modo "solo lectura" opcional para la API de FerroAnalytics.

Si se define la variable de entorno FERRO_API_KEY, toda ruta que mute datos
(POST/PUT/PATCH/DELETE: importar CSV, importar desde BD, deshacer un lote de
movimientos) exige el header `X-API-Key` con ese valor exacto; las lecturas
(GET) siguen abiertas siempre. Sin FERRO_API_KEY definida (el caso por
defecto en desarrollo), no se exige nada y el comportamiento no cambia.

Pensado para compartir el dashboard (con un profesor, con la ferretería) sin
exponer operaciones destructivas como DELETE /movimientos/lotes/{lote} o las
importaciones, sin tener que montar un sistema de usuarios completo: quien
tiene la clave puede seguir mutando datos (guardándola una vez en el
dashboard), quien no, solo puede consultar.
"""

import os

from fastapi import Header, HTTPException, Request

_METODOS_DE_SOLO_LECTURA = {"GET", "HEAD", "OPTIONS"}


def clave_configurada() -> str | None:
    """La clave activa, o None si el modo solo lectura está desactivado."""
    return os.environ.get("FERRO_API_KEY") or None


def modo_solo_lectura_activo() -> bool:
    """Indica si hay una FERRO_API_KEY configurada (lo que expone /api/salud)."""
    return clave_configurada() is not None


async def exigir_clave_para_mutaciones(
    request: Request, x_api_key: str | None = Header(default=None),
) -> None:
    """
    Dependency global (ver api/main.py): deja pasar cualquier lectura, y
    cualquier método si no hay FERRO_API_KEY definida. Si la hay, exige que
    X-API-Key coincida exactamente para mutar datos.
    """
    clave = clave_configurada()
    if clave is None or request.method in _METODOS_DE_SOLO_LECTURA:
        return
    if x_api_key != clave:
        raise HTTPException(
            status_code=403,
            detail=(
                "Esta acción requiere la clave de la API (header X-API-Key): "
                "el dashboard está en modo solo lectura."
            ),
        )
