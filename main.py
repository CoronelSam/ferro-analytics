"""
Punto de entrada de FerroAnalytics.
Ejecutar con: python main.py
"""

from dotenv import load_dotenv

load_dotenv()  # variables opcionales en .env (p. ej. FERRO_BD_URL), antes de leer nada de src/

from src.menu import ejecutar

if __name__ == "__main__":
    ejecutar()
