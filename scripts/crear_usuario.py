"""
Crea un usuario para iniciar sesión en el dashboard de FerroAnalytics
(ver api/usuarios.py). Pide la contraseña de forma interactiva: no queda
en el historial de la terminal ni en la lista de procesos.

Uso (desde la raíz del proyecto):
    python scripts/crear_usuario.py admin "Administradora" --rol admin
    python scripts/crear_usuario.py jperez "Juan Pérez"
"""

import argparse
import getpass
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from api import usuarios as usr  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Crea un usuario del dashboard de FerroAnalytics.")
    parser.add_argument("usuario", help="Nombre de usuario para iniciar sesión")
    parser.add_argument("nombre", help="Nombre para mostrar en el dashboard")
    parser.add_argument("--rol", default="usuario", choices=["usuario", "admin"])
    args = parser.parse_args()

    contrasena = getpass.getpass("Contraseña: ")
    confirmacion = getpass.getpass("Confirmar contraseña: ")
    if contrasena != confirmacion:
        print("Las contraseñas no coinciden.", file=sys.stderr)
        raise SystemExit(1)

    try:
        usr.crear_usuario(args.usuario, args.nombre, contrasena, rol=args.rol)
    except ValueError as error:
        print(error, file=sys.stderr)
        raise SystemExit(1)

    print(f"Usuario '{args.usuario}' creado.")


if __name__ == "__main__":
    main()
