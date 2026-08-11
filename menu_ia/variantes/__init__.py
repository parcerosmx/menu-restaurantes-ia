"""Qué VARIANTE de idioma se pide y cómo se llaman sus archivos.

    pedido()   lee `--idioma`      ·  sufijo("en") → "-en"
    ruta(p, i) → `menu-completo-en.html`

⚠️ **Se llamaba `idiomas`, y eso era una trampa.** El proyecto del cliente
tiene su propio paquete `idiomas/` con los catálogos de traducción —el motor lo
carga por nombre suelto (`importlib.import_module("idiomas.en")`)—, así que un
`import idiomas` en un script del cliente resolvía al catálogo y fallaba con
`AttributeError: module has no attribute 'pedido'`. Dos cosas distintas con el
mismo nombre, y la que ganaba dependía del `sys.path`.

Esto decide la VARIANTE; `idiomas/` del proyecto tiene el CONTENIDO.
"""
import os
import sys

# Idiomas con catálogo. `es` es la fuente y no tiene archivo.
DISPONIBLES = ("es", "en")


def pedido(argv=None):
    """Idioma pedido en la línea de comandos, o `MENU_IDIOMA`, o español.

    ⚠️ Se lee a mano y NO con argparse. `build_menu.py` hace su trabajo al
    importarse, y cuatro scripts del repo lo cargan por ruta
    (`items_menu.py`, `build_precios.py`, `build_habladores.py`,
    `push_textos.py`). Con argparse, ese import heredaría el `sys.argv` del
    script que lo carga y `build_precios.py --lo-que-sea` moriría dentro de
    `build_menu.py`, con un error que no menciona ni a uno ni a otro.
    """
    argv = sys.argv if argv is None else argv
    if "--idioma" in argv:
        i = argv.index("--idioma")
        if i + 1 >= len(argv):
            raise SystemExit("⛔ --idioma necesita un código (es, en)")
        codigo = argv[i + 1].lower()
    else:
        codigo = os.environ.get("MENU_IDIOMA", "es").lower()
    if codigo not in DISPONIBLES:
        raise SystemExit(
            f"⛔ Idioma «{codigo}» desconocido. Hay: {', '.join(DISPONIBLES)}")
    return codigo


def sufijo(codigo=None):
    """`''` para español, `'-en'` para inglés."""
    codigo = pedido() if codigo is None else codigo
    return "" if codigo == "es" else f"-{codigo}"


def ruta(p, codigo=None):
    """Mete el sufijo de idioma antes de la extensión de un Path."""
    return p.with_name(f"{p.stem}{sufijo(codigo)}{p.suffix}")
