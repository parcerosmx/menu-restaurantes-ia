#!/usr/bin/env python3
"""Levanta el esqueleto de un proyecto nuevo. Determinista, sin preguntar nada.

Reparto de trabajo
------------------
Esto **genera archivos a partir de un JSON**. La entrevista —qué restaurante,
qué formato, qué carta— la hace el skill `crear-menu`, que es lo que sabe
hablar con una persona y leer la foto de una carta vieja.

La separación no es burocracia: un generador que pregunta no se puede correr
dos veces igual, ni probar, ni meter en un guion. Este se corre con el mismo
JSON y da el mismo proyecto.

    menu-ia crear --desde brief.json --en ~/src/mi-restaurante

Qué deja
--------
Lo mínimo que el motor exige de un proyecto, y ni un archivo más:

    <destino>/
      render/
        style.css            los dos bloques de tokens, con sus centinelas
        temas/__init__.py    la identidad: paleta, letras, lema
        piel-<slug>.css      la capa visual — ESTO es lo que hay que diseñar
        carta/__init__.py    los platillos, el orden, el título
        recetas.py           las recetas propias (vacío al principio)
      .env                   MENU_PROYECTO, para no exportarlo a mano

⚠️ **El proyecto queda funcionando, no terminado.** La piel que se genera es
un punto de partida sobrio y honesto: tipografía del sistema, una tinta de
acento, sin ornamentos. Sirve para ver la carta montada el primer día; no es
la identidad de nadie. Eso es un encargo de diseño y el motor no lo suple.

El JSON
-------
    {
      "nombre":   "La Cantina del Puerto",
      "slug":     "cantina",
      "formato":  "a4-hoja",
      "lema":     "Cocina de puerto",
      "colores":  {"papel": "#FBFAF7", "tinta": "#14110E",
                   "acento": "#8C1D18", "gris": "#6E6A65"},
      "hojas": [
        {"seccion": "Para comer", "slug": "comer", "arquetipo": "hoja",
         "items": [{"n": "Ceviche", "precio": "195", "desc": "…"}]}
      ]
    }

Solo `nombre`, `slug`, `formato` y `hojas` son obligatorios.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import formato as _formato

# Paleta de arranque. Neutra a propósito: si el motor propusiera colores
# «bonitos», el primer cliente los dejaría puestos y saldría a imprenta con la
# identidad por omisión de una herramienta.
COLORES = {"papel": "#FFFFFF", "tinta": "#1A1A1A",
           "acento": "#7A7A7A", "gris": "#6E6E6E", "filete": "#DDDDDD",
           "placeholder-foto": "#E6E6E6", "placeholder-texto": "#8A8A8A"}

FUENTES = {"cuerpo": "Helvetica, Arial, sans-serif",
           "display": "Georgia, 'Times New Roman', serif",
           "badge": "Georgia, 'Times New Roman', serif",
           "script": "Georgia, 'Times New Roman', serif"}


def _tokens_css(colores, fuentes):
    """`style.css` con los DOS bloques generados y sus centinelas.

    Sin los centinelas, `formato.py --aplicar` y `tema.py --aplicar` no tienen
    dónde escribir y el proyecto nace con las guardas en rojo.
    """
    from .motor.tema_base import FIN as TFIN, INI as TINI
    from .formato import FIN as FFIN, INI as FINI
    tk = "\n".join(f"  --{k}: {v};" for k, v in colores.items())
    ft = "\n".join(f"  --font-{k}: {v};" for k, v in fuentes.items())
    return (f"/* Tokens del proyecto. Los DOS bloques los generan\n"
            f"   `menu-ia`; entre los centinelas no se edita a mano. */\n\n"
            f":root {{\n{TINI}\n{tk}\n\n{ft}\n{TFIN}\n\n"
            f"{FINI}\n  --page-w: 0mm;\n  --page-h: 0mm;\n"
            f"  --bleed: 0mm;\n  --margen-exterior: 0mm;\n{FFIN}\n}}\n")


def _temas_py(nombre, slug, lema, colores, fuentes):
    c = "\n".join(f'            "{k}": "{v}",' for k, v in colores.items())
    f = "\n".join(f'            "{k}": "{v}",' for k, v in fuentes.items())
    return (f'"""La identidad de {nombre}. La clase `Tema` la pone el motor.\n\n'
            f'Un tema son los VALORES. Las FORMAS —cómo es el rótulo de\n'
            f'sección, si hay sello, qué adorna una portadilla— viven en\n'
            f'`piel-{slug}.css`. Cambiar solo estos tokens da la piel de\n'
            f'arranque en otros colores, que no es una identidad.\n"""\n'
            f'from menu_ia.motor.tema_base import Tema\n\n'
            f'TEMAS = {{\n    "{slug}": Tema(\n'
            f'        nombre="{slug}",\n        colores={{\n{c}\n        }},\n'
            f'        fuentes={{\n{f}\n        }},\n'
            f'        css_piel="piel-{slug}.css",\n'
            f'        ornamentos={{}},   # ninguno todavía\n'
            f'        lema={lema!r},\n    ),\n}}\n')


def _piel_css(nombre, slug):
    return f"""/* PIEL «{slug}» — la capa visual de {nombre}.

   ⚠️ ESTO ES UN PUNTO DE PARTIDA, NO UN DISEÑO. Tipografía del sistema, una
   tinta de acento, cero ornamentos. Existe para que la carta se pueda ver
   montada el primer día y para que se note qué falta.

   Lo que el motor NO pone y hay que decidir: cómo es el rótulo de sección,
   qué hace el precio, si hay foto y dónde, qué adorna una portadilla. Eso es
   la identidad del restaurante y es un encargo de diseño.

   `estructura.css` —la mecánica de página— la trae el motor y no se toca.
*/

html, body {{ background: #fff; color: var(--tinta); }}
@media screen {{ body {{ background: #3a3a38; }} }}

.page {{
  --fondo: var(--papel);
  --texto: var(--tinta);
  background: var(--fondo);
  color: var(--texto);
  font-family: var(--font-cuerpo);
}}
.lista-page {{ background: var(--papel); }}

.badge-seccion, .lista-header .badge-seccion {{
  background: none; color: var(--tinta);
  font-family: var(--font-display); font-weight: 400;
  font-size: 15pt; letter-spacing: 3px; text-transform: uppercase;
  transform: none; border-radius: 0;
  border-bottom: 0.5mm solid var(--acento);
}}
.badge-seccion::before {{ content: none; }}

.lista-densa .mini-titulo, .mini-titulo {{
  font-family: var(--font-display); font-size: 8.5pt;
  letter-spacing: 2.5px; text-transform: uppercase; color: var(--acento);
}}
.denso-item .nombre-display, .nombre-display {{
  font-family: var(--font-display); font-size: 9.5pt;
  font-weight: 600; color: var(--tinta);
}}
.nombre-unidades {{ font-family: var(--font-cuerpo); font-size: 7pt;
  color: var(--gris); }}
.desc {{ font-family: var(--font-cuerpo); font-size: 7.2pt;
  line-height: 1.45; color: var(--gris); }}
.desc-gancho {{ font-style: italic; color: var(--tinta); }}

/* El precio va pegado al nombre, NUNCA en columna alineada ni con puntos
   guía. No es gusto: una carta con los precios en columna se lee como un
   comparador y baja el ticket. */
.precio {{ font-family: var(--font-cuerpo); font-size: 11.5pt;
  font-weight: 600; color: var(--acento); }}

.pie {{ font-family: var(--font-cuerpo); font-size: 6.5pt;
  letter-spacing: 2px; text-transform: uppercase; color: var(--gris);
  border-top: 0.2mm solid var(--filete); background: none; }}
"""


def _carta_py(nombre, hojas):
    def item(it):
        campos = ", ".join(f'"{k}": {v!r}' for k, v in it.items())
        return f"        {{{campos}}},"
    bloques = []
    for h in hojas:
        its = "\n".join(item(i) for i in h.get("items", []))
        bloques.append(
            f'_{h["slug"]} = {{\n'
            f'    "seccion": {h["seccion"]!r},\n'
            f'    "slug": {h["slug"]!r},\n'
            f'    "arquetipo": {h.get("arquetipo", "hoja")!r},\n'
            f'    "items": [\n{its}\n    ],\n}}\n')
    orden = ", ".join(repr(h["slug"]) for h in hojas)
    nombres = ", ".join(f'_{h["slug"]}' for h in hojas)
    return (f'"""La carta de {nombre}: los platillos, su orden y el título.\n\n'
            f'Esto es lo único que hay que mantener al día. Un precio se\n'
            f'escribe UNA vez; si un producto aparece en dos hojas, la\n'
            f'segunda lo lee de la primera — el build se planta si el mismo\n'
            f'producto queda impreso a dos precios distintos.\n"""\n\n'
            + "\n".join(bloques)
            + f'\nSPREADS = [{nombres}]\n\n'
            f'# El orden de impresión. Es una decisión tuya sobre tus\n'
            f'# platillos, no del motor sobre cómo dibuja.\nORDEN = [{orden}]\n\n'
            f'TITULO = {{"es": {nombre + " — Carta"!r}}}\n\n'
            f'# Scripts de este proyecto que también producen HTML\n'
            f'# verificable (tapas, por ejemplo). Vacío es válido.\n'
            f'PRODUCTORES_HTML = []\n')


def crear(brief, destino):
    slug = brief["slug"]
    nombre = brief["nombre"]
    fmt = brief["formato"]
    if fmt not in _formato.FORMATOS:
        raise SystemExit(f"⛔ Formato «{fmt}» desconocido. "
                         f"Conocidos: {', '.join(_formato.FORMATOS)}")

    colores = {**COLORES, **brief.get("colores", {})}
    fuentes = {**FUENTES, **brief.get("fuentes", {})}
    hojas = brief["hojas"]

    # La cuenta contra el formato ANTES de escribir nada. Un proyecto que nace
    # sin poder construirse es peor que uno que no nace.
    f = _formato.FORMATOS[fmt]
    paginas = sum(2 if h.get("arquetipo", "hoja") == "pliego" else 1
                  for h in hojas)
    err = f.comprobar_paginas(paginas)
    if err:
        raise SystemExit(err + f"\n   («{fmt}» admite "
                               f"{f.paginas_contenido} de contenido.)")

    d = Path(destino).expanduser().resolve()
    r = d / "render"
    (r / "temas").mkdir(parents=True, exist_ok=True)
    (r / "carta").mkdir(parents=True, exist_ok=True)

    (r / "style.css").write_text(_tokens_css(colores, fuentes), encoding="utf-8")
    (r / "temas" / "__init__.py").write_text(
        _temas_py(nombre, slug, brief.get("lema", ""), colores, fuentes),
        encoding="utf-8")
    (r / f"piel-{slug}.css").write_text(_piel_css(nombre, slug), encoding="utf-8")
    (r / "carta" / "__init__.py").write_text(_carta_py(nombre, hojas),
                                             encoding="utf-8")
    (r / "recetas.py").write_text(
        '"""Recetas y comprobaciones propias. El motor trae las genéricas.\n\n'
        'from menu_ia.receta import Receta\n'
        'RECETAS = [Receta("tapas", "…", [("build_tapas.py", [])])]\n'
        'COMPROBACIONES = [("…", "mi_script.py", [])]\n"""\n'
        'RECETAS = []\nCOMPROBACIONES = []\n', encoding="utf-8")
    (d / ".env").write_text(
        f"# Para no exportarlo a mano en cada terminal.\n"
        f"MENU_PROYECTO={r}\nMENU_CARTA=carta\nMENU_TEMA={slug}\n"
        f"MENU_FORMATO={fmt}\n", encoding="utf-8")

    print(f"✅ Proyecto «{nombre}» creado en {d}\n")
    print(f"   formato   {fmt} · {f.paginas} páginas · {f.encuadernacion}")
    print(f"   contenido {len(hojas)} hoja(s) · {paginas} página(s)\n")
    print("   Para construirlo:\n")
    print(f"     cd {d}")
    print(f"     export MENU_PROYECTO={r} MENU_CARTA=carta "
          f"MENU_TEMA={slug} MENU_FORMATO={fmt}")
    print(f"     python3 -m menu_ia.formato --aplicar")
    print(f"     python3 -m menu_ia.tema --aplicar")
    print(f"     menu-ia menu\n")
    print(f"   ⚠️ `piel-{slug}.css` es un punto de partida, no un diseño.")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--desde", required=True, help="el JSON del encargo")
    ap.add_argument("--en", required=True, help="dónde crear el proyecto")
    args = ap.parse_args()
    brief = json.loads(Path(args.desde).read_text(encoding="utf-8"))
    for k in ("nombre", "slug", "formato", "hojas"):
        if k not in brief:
            raise SystemExit(f"⛔ Al encargo le falta «{k}».")
    return crear(brief, args.en)


if __name__ == "__main__":
    sys.exit(main())
