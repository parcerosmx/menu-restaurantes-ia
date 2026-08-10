"""rutas — extraído de `build_menu.py`.

⚠️ El REPARTO de este archivo lo genera `herramientas/partir_build_menu.py`.
   Si algo está en el módulo equivocado, se ajusta el MANIFIESTO del
   splitter y se vuelve a correr — no se mueve a mano.
   El CONTENIDO (platillos, precios, textos) sí se edita aquí.
"""
from pathlib import Path

REND = Path(__file__).resolve().parent.parent

A = "../assets/ejemplo"

def src_de(path):
    return f"../assets/{path}" if "/" in path else f"{A}/{path}"
