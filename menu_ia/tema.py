#!/usr/bin/env python3
"""La identidad visual: paleta, tipografías y los roles que cumplen.

Hermano de `formato.py`. Aquel dice cuánto mide el papel; este dice de qué
color y con qué letra se pinta encima.

Por qué existe
--------------
La paleta y las tipografías vivían dentro de `style.css`, mezcladas con las
reglas que las usan. Mientras hubo un solo restaurante daba igual. En cuanto
hay dos, cambiar la identidad significaba editar a mano una hoja de estilo de
300 líneas y confiar en no haberse dejado un `#EB5D3F` suelto.

Aquí la identidad es **dato**: un diccionario de tokens que genera su bloque
`:root`. Cambiar de marca es cambiar de tema, no de CSS.

⚠️ **Un tema NO es una piel.** Esto son los VALORES —qué naranja, qué letra—.
Las FORMAS —la cinta rasgada del badge, el sello circular, el subrayado de
brochazo— son otra cosa y viven en `piel-<cliente>.css`. Cambiar solo los
tokens da «Parceros en otros colores», que es justo lo que el roadmap dice que
no basta.

📌 **`style-guide.md` sigue siendo la autoridad.** Este módulo transcribe lo
que ese archivo decidió; si discrepan, se corrige este.

Uso
---
    python3 render/tema.py              # enseña el tema activo
    python3 render/tema.py --aplicar    # sincroniza el bloque de style.css
    python3 render/tema.py --verificar  # ¿concuerda? (lo usa el build)

    MENU_TEMA=<nombre> python3 render/hacer.py menu
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

REND = Path(__file__).resolve().parent



from motor.tema_base import FIN, INI, Tema  # noqa: F401


# ════════════════════════════════════════════════════════════════════════
#  De dónde salen los temas
# ════════════════════════════════════════════════════════════════════════
# El motor trae la CLASE, no los temas. Un tema es identidad —paleta, letras,
# ornamentos, lema— y eso es del cliente. Mientras los temas vivieron aquí, el
# paquete público se llevaba dentro el sello de Parceros.
import importlib  # noqa: E402

MODULO_TEMAS = os.environ.get("MENU_TEMAS", "temas")
try:
    TEMAS = importlib.import_module(MODULO_TEMAS).TEMAS
except ModuleNotFoundError:
    TEMAS = {}

NOMBRE_ACTIVO = os.environ.get("MENU_TEMA", "parceros")
if NOMBRE_ACTIVO not in TEMAS:
    raise SystemExit(f"⛔ MENU_TEMA=«{NOMBRE_ACTIVO}» no existe. "
                     f"Conocidos: {', '.join(TEMAS)}")

ACTIVO = TEMAS[NOMBRE_ACTIVO]


# ── Sincronización con style.css ────────────────────────────────────────
# Mismo trato que `formato.py`: el build VERIFICA y se planta; no reescribe un
# archivo rastreado a tus espaldas.
def _style():
    return REND / "style.css"


def bloque_actual(texto=None):
    texto = _style().read_text(encoding="utf-8") if texto is None else texto
    m = re.search(re.escape(INI) + r".*?" + re.escape(FIN), texto, re.S)
    return m.group(0) if m else None


def aplicar():
    ruta = _style()
    texto = ruta.read_text(encoding="utf-8")
    actual, nuevo = bloque_actual(texto), ACTIVO.bloque_css()
    if actual is None:
        raise SystemExit("⛔ No encuentro el bloque de tema en style.css.\n"
                         f"   Tiene que existir entre:\n     {INI}\n     {FIN}")
    texto = texto.replace(actual, nuevo)
    # El `@import` de las fuentes va fuera del `:root`, así que se sustituye
    # aparte. Va primero en el archivo: un `@import` después de una regla lo
    # ignora el navegador, en silencio.
    if ACTIVO.import_fuentes:
        texto = re.sub(r"@import url\('[^']*'\);",
                       f"@import url('{ACTIVO.import_fuentes}');", texto, count=1)
    if texto == ruta.read_text(encoding="utf-8"):
        print(f"✅ style.css ya concuerda con el tema «{ACTIVO.nombre}».")
        return 0
    ruta.write_text(texto, encoding="utf-8")
    print(f"✅ style.css sincronizado con el tema «{ACTIVO.nombre}».")
    return 0


def verificar():
    actual = bloque_actual()
    if actual is None:
        print("⛔ style.css no tiene el bloque de tema generado.")
        return 1
    if actual != ACTIVO.bloque_css():
        print(f"⛔ style.css NO concuerda con el tema «{ACTIVO.nombre}».\n"
              "   Arréglalo con:  python3 render/tema.py --aplicar")
        return 1
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--verificar", action="store_true")
    args = ap.parse_args()

    if args.aplicar:
        return aplicar()
    if args.verificar:
        r = verificar()
        if r == 0:
            print(f"✅ style.css concuerda con el tema «{ACTIVO.nombre}».")
        return r

    print(ACTIVO)
    print(f"\nTemas conocidos: {', '.join(TEMAS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
