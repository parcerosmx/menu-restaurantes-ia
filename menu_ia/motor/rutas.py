"""Dónde están los archivos del cliente, desde el punto de vista del motor.

⚠️ `REND` **ya no se deduce de la ubicación de este archivo**. Lo hacía
—`Path(__file__).parent.parent`— y eso daba la respuesta correcta solo mientras
el motor vivía dentro del repo del cliente. Instalado como paquete apuntaba a
`site-packages/menu_ia/`, donde no hay ni un `style.css`.

Lo resuelve `proyecto.py`. El nombre `REND` se conserva porque lo leen varios
módulos y renombrarlo no aporta nada.
"""
from ..proyecto import RAIZ as REND  # noqa: F401

A = "../assets/ejemplo"

def src_de(path):
    return f"../assets/{path}" if "/" in path else f"{A}/{path}"
