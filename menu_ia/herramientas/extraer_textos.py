#!/usr/bin/env python3
"""Saca la lista EXACTA de textos que hay que traducir, en orden de render.

Por qué renderizando y no leyendo los archivos
==============================================
La forma obvia era barrer `secciones/*.py` con el AST y recoger los valores de
`desc`, `n`, `nota`… Se probó y da una lista que **no sirve como encargo de
traducción**, por tres motivos que cuestan una ronda cada uno:

  · Recoge lo que NO se imprime: los platillos con `"activo": False` (Arepas
    Quesudas, la hoja de Brunch entera) y los textos de zonas que ninguna hoja
    activa ejercita. Traducir eso es trabajo que nadie ve.
  · No recoge lo que sí se imprime y no vive en los datos: «El favorito»,
    «Adiciones», «Agrégale más sabor», el lema del pie. Esos textos están en
    el motor, y son los que más se repiten en el menú.
  · Pierde el orden. Un traductor que lee «Truena al morderlo…» sin las tres
    líneas que van antes en la misma página no puede juzgar si repite un
    gancho que ya usó la ficha de al lado — y en este menú eso importa
    (§6.55: «Así» en vez de «Como» solo para no ecoar a la ficha de arriba).

Se renderiza con la captura de `motor/idioma.py` encendida, así que lo que sale
es literalmente lo que Chromium va a pintar.

Uso
---
    python3 render/herramientas/extraer_textos.py            # informe legible
    python3 render/herramientas/extraer_textos.py --faltan   # solo lo no traducido
    python3 render/herramientas/extraer_textos.py --esqueleto  # plantilla py
"""
import argparse
import importlib.util
import sys
from pathlib import Path

# La raíz es la del CLIENTE, no la del paquete: aquí están su HTML, su
# CSS y sus datos. Deducirla de `__file__` daba site-packages.
from ..proyecto import RAIZ as REND
sys.path.insert(0, str(REND))

from ..motor import idioma  # noqa: E402


def textos_impresos():
    """Renderiza el menú con la captura encendida y devuelve los textos únicos
    en orden de aparición."""
    idioma.CAPTURA = []
    spec = importlib.util.spec_from_file_location("_bm", REND / "build_menu.py")
    mod = importlib.util.module_from_spec(spec)
    # `build_menu.py` escribe el HTML como efecto de importarse. Es lo que
    # queremos: el render completo es justo lo que dispara cada `t()`.
    import contextlib
    import io
    with contextlib.redirect_stdout(io.StringIO()):
        spec.loader.exec_module(mod)
    capturados = idioma.CAPTURA
    idioma.CAPTURA = None

    vistos, orden = set(), []
    for s in capturados:
        clave = idioma._norm(s)
        if clave in vistos or not any(c.isalpha() for c in clave):
            continue
        vistos.add(clave)
        orden.append(clave)
    return orden


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--faltan", action="store_true",
                    help="solo los que aún no tienen traducción")
    ap.add_argument("--esqueleto", action="store_true",
                    help="imprime una plantilla lista para pegar en idiomas/")
    ap.add_argument("--idioma", default="en")
    args = ap.parse_args()

    todos = textos_impresos()

    ya = {}
    try:
        idioma.fijar(args.idioma)
        ya = dict(idioma._CATALOGO)
    except SystemExit:
        pass          # todavía no existe el catálogo — es el caso del día 1
    finally:
        idioma.fijar("es")

    faltan = [s for s in todos if s not in ya]

    if args.esqueleto:
        print(f"TEXTOS = {{")
        for s in (faltan if args.faltan else todos):
            literal = repr(s)
            print(f"    {literal}:")
            print(f"        ,")
        print("}")
        return

    lista = faltan if args.faltan else todos
    for s in lista:
        marca = "  " if s in ya else "🔴"
        print(f"{marca} {s}")
    print(f"\n{len(todos)} textos impresos · {len(todos) - len(faltan)} traducidos "
          f"· {len(faltan)} pendientes")


if __name__ == "__main__":
    main()
