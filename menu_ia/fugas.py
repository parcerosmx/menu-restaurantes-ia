#!/usr/bin/env python3
"""¿Se le escapa al motor la marca de otro cliente? Monta un canario y mira.

Por qué existe
--------------
Este fallo **ninguna guarda del cliente original puede verlo**, y no por
descuido: por construcción. Si el motor lleva escrito «De corazón y sabor.»,
los PNG de Parceros salen byte a byte idénticos, `comprobar` da verde y la
geometría cuadra — porque esa cadena ES su lema. El fallo solo existe para el
SIGUIENTE cliente.

Ya pasó tres veces:

  · El sello llevaba «DE CORAZÓN Y SABOR · PARCEROS» dentro del SVG.
  · El PDF declaraba `producer: "Parceros Café"` en sus metadatos — invisible
    en la página, visible al abrir Propiedades, y para entonces ya está en el
    taller.
  · El pie volvió a decir el lema de Parceros **después de arreglarlo**: el
    arreglo se perdió al copiar el motor de un repo al otro, y nadie lo notó
    hasta montar una panadería.

La única forma de verlo es **montar un cliente nuevo y mirarle cada
superficie**. Eso es lo que hace esto, y por eso no se hace a mano.

Cómo funciona
-------------
Levanta un proyecto **canario** con valores imposibles de confundir —nombre
`ZZQQ`, lema `XKCD-LEMA-CANARIO`, magenta puro—, lo construye entero y barre
cada superficie por la que la marca puede escapar:

    el <title> del HTML          el pie de página
    los ornamentos               los metadatos del PDF (title, producer, …)
    el nombre de los archivos    el texto impreso

Y comprueba las dos direcciones, que es lo que importa:

  1. **Que no aparezca nada ajeno** — ninguna palabra de la lista de vigilancia.
  2. **Que SÍ aparezca lo del canario** — si el lema del canario no está en el
     pie, algo lo está pisando aunque no se vea de quién.

Lo segundo es lo que caza un valor por omisión: un motor que no pinta nada
pasa la primera comprobación y falla esta.

Uso
---
    python3 -m menu_ia.fugas
    python3 -m menu_ia.fugas --conservar   # deja el canario para mirarlo
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PY = sys.executable

# Palabras que NO pueden aparecer en lo que produce un cliente cualquiera.
# Son de los proyectos que han pasado por este motor; al añadir un cliente
# nuevo, sus marcas se añaden aquí.
VIGILADAS = [
    "Parceros", "parceros", "De corazón y sabor", "corazón y sabor",
    "Cantina del Puerto", "cantina",
]

# Lo que el canario declara y TIENE que aparecer donde corresponde.
CANARIO = {
    "nombre": "ZZQQ Canario Test",
    "slug": "zzqqcanario",
    "formato": "a4-hoja",
    "lema": "XKCD-LEMA-CANARIO",
    "colores": {"papel": "#FFFFFF", "tinta": "#000000", "acento": "#FF00FF"},
    "hojas": [
        {"seccion": "Alfa", "slug": "alfa", "arquetipo": "hoja", "items": [
            {"n": "Producto Uno", "precio": "11",
             "desc": "Gancho uno.\nCuerpo uno."}]},
        {"seccion": "Beta", "slug": "beta", "arquetipo": "hoja", "items": [
            {"n": "Producto Dos", "precio": "22"}]},
    ],
}


def _correr(mod, args, cwd, env):
    r = subprocess.run([PY, "-m", mod, *args], cwd=cwd, env=env,
                       capture_output=True, text=True)
    return r.returncode == 0, (r.stdout + r.stderr)


def revisar(base):
    import os
    d = Path(base) / CANARIO["slug"]
    brief = Path(base) / "brief.json"
    brief.write_text(json.dumps(CANARIO), encoding="utf-8")

    ok, sal = _correr("menu_ia.crear", ["--desde", str(brief), "--en", str(d)],
                      base, os.environ.copy())
    if not ok:
        print(sal[-800:])
        return ["no se pudo crear el canario"]

    env = {**os.environ, "MENU_PROYECTO": str(d / "render"),
           "MENU_CARTA": "carta", "MENU_TEMA": CANARIO["slug"],
           "MENU_FORMATO": CANARIO["formato"]}
    for mod, a in (("menu_ia.formato", ["--aplicar"]),
                   ("menu_ia.tema", ["--aplicar"]),
                   ("menu_ia.build_menu", []),
                   ("menu_ia.build_pdf_plano", ["--web"])):
        ok, sal = _correr(mod, a, d, env)
        if not ok:
            print(sal[-800:])
            return [f"el canario no construye: {mod}"]

    fallos = []
    html = (d / "render" / "menu-completo.html").read_text(encoding="utf-8")
    # El CSS va incrustado y sus comentarios son documentación, no salida: lo
    # que se vigila es lo que se IMPRIME.
    visible = re.sub(r"<style.*?</style>", " ", html, flags=re.S)
    visible = re.sub(r"<[^>]+>", " ", visible)

    for pal in VIGILADAS:
        if pal in visible:
            fallos.append(f"«{pal}» aparece en el TEXTO IMPRESO del canario")

    # 2 · lo que SÍ tiene que estar
    if CANARIO["lema"] not in visible:
        fallos.append(f"el lema del canario NO sale en el pie "
                      f"— algo lo pisa o el pie no lo pinta")
    if CANARIO["nombre"] not in html:
        fallos.append("el nombre del canario NO sale en el <title>")

    # 3 · los PDF: metadatos y nombre de archivo
    import fitz
    for pdf in sorted((d / "output").rglob("*.pdf")):
        for pal in VIGILADAS:
            if pal.lower() in pdf.name.lower():
                fallos.append(f"«{pal}» en el NOMBRE de {pdf.name}")
        doc = fitz.open(pdf)
        m = doc.metadata or {}
        for k in ("title", "author", "subject", "keywords", "producer", "creator"):
            v = (m.get(k) or "")
            for pal in VIGILADAS:
                if pal in v:
                    fallos.append(f"«{pal}» en el metadato {k} de {pdf.name}")
        doc.close()

    return fallos


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--conservar", action="store_true",
                    help="no borra el canario al terminar")
    args = ap.parse_args()

    base = Path(tempfile.mkdtemp(prefix="canario-"))
    try:
        print(f"\n\033[1m▶ fugas de marca\033[0m — canario en {base}\n")
        fallos = revisar(base)
        for f in fallos:
            print(f"  🔴 {f}")
        if fallos:
            print(f"\n\033[1m⛔ {len(fallos)} fuga(s).\033[0m El motor le está "
                  "pasando la marca de un cliente a otro.")
            return 1
        print("  ✅ nada ajeno en el texto impreso")
        print("  ✅ nada ajeno en los metadatos ni en los nombres de archivo")
        print("  ✅ el lema y el nombre del canario salen donde deben")
        print("\n\033[1m✅ El motor no filtra marca.\033[0m")
        return 0
    finally:
        if args.conservar:
            print(f"\n   canario conservado en {base}")
        else:
            shutil.rmtree(base, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
