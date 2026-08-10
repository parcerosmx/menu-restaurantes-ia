#!/usr/bin/env python3
"""Arma `menu-completo.html` a partir de las hojas de `secciones/`.

Este archivo ya NO tiene contenido: solo decide el ORDEN DE IMPRESIÓN,
monta las hojas activas y escribe el HTML. Para cambiar un platillo,
un precio o una foto, el archivo es `secciones/<hoja>.py`.

    render/
      secciones/   una hoja por archivo — el contenido
      carta/       precios de fuente única (adiciones, café, bebidas)
      motor/       cómo se dibuja — casi nunca se toca
"""
import sys
from pathlib import Path

# `items_menu.py` y compañía cargan este archivo por RUTA (`spec_from_file_location`),
# y por esa vía Python no añade `render/` al path. Sin esto, los `import` de
# abajo fallan según desde dónde se llame.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import json

import idiomas
from motor import idioma

# ⚠️ VA ANTES QUE CUALQUIER IMPORT DE `secciones`/`carta`: el catálogo tiene
# que estar activo cuando el motor empiece a pedir traducciones. Fijarlo
# después dejaría en español lo que se resolviera durante el import.
IDIOMA = idiomas.pedido()
idioma.fijar(IDIOMA)

from motor.iconos import TICK
from motor.pagina import pagina, paginas_de
from motor.rutas import REND

# 📖 La CARTA — qué restaurante se maqueta. Por omisión Parceros
# (`secciones/`); `MENU_CARTA` la cambia sin tocar código, igual que
# `MENU_FORMATO` y `MENU_TEMA`.
#
# El paquete de una carta expone dos cosas: `SPREADS` (sus hojas) y `ORDEN`
# (en qué orden se imprimen). `ORDEN` vivía aquí, y estaba bien mientras hubo
# un solo restaurante: en cuanto hay dos, el orden es del cliente, no del
# motor.
import importlib
import os

CARTA = os.environ.get("MENU_CARTA", "secciones")
_carta = importlib.import_module(CARTA)
SPREADS = _carta.SPREADS

# ── Reexportes de la carta de Parceros ──────────────────────────────────
# ⚠️ Esto NO es superficie del motor: es un puente de compatibilidad.
# `items_menu.py`, `build_precios.py`, `build_habladores.py` y
# `push_textos.py` cargan ESTE archivo por ruta y leen `ADICIONES`, `CAFE` y
# `BEBIDAS_FAMILIAS` como atributos suyos. Son datos de `carta/`, o sea de
# Parceros — y mientras estuvieran importados arriba, el motor no arrancaba
# sin ellos: un paquete que exige el contenido de otro cliente para importarse
# no es un paquete.
#
# Ahora es opcional. Una carta sin `carta/` —la demo, o cualquier cliente
# nuevo— importa igual; lo que no tendrá es este puente, y los cuatro scripts
# que lo usan son de Parceros de todos modos.
#
# 📌 La salida definitiva es que esos cuatro lean de `carta` directamente, no
# a través del motor. Queda anotado para la Fase 4b.
try:
    from carta.adiciones import ADICIONES, GRUPOS_PIE, SOLO_BLOQUE
    from carta.bebidas import BEBIDAS_FAMILIAS
    from carta.cafe import CAFE, CAFE_COMBO, CAFE_FRASE
    from carta.precios import precio_bebida, precio_jarra_min
except ModuleNotFoundError:
    ADICIONES = GRUPOS_PIE = SOLO_BLOQUE = None
    BEBIDAS_FAMILIAS = CAFE = CAFE_COMBO = CAFE_FRASE = None
    precio_bebida = precio_jarra_min = None

# ── Superficie pública ──────────────────────────────────────────────
# `items_menu.py`, `build_precios.py`, `build_habladores.py` y
# `push_textos.py` cargan este archivo por ruta y leen estos nombres como
# atributos del módulo. Los `import` de arriba ya los dejan disponibles;
# `__all__` está para que se vea que es un contrato y no una casualidad.
__all__ = [
    "IDIOMA",
    "SPREADS",
    "ORDEN",
    "ACTIVOS",
    "INACTIVOS",
    "ADICIONES",
    "SOLO_BLOQUE",
    "GRUPOS_PIE",
    "CAFE",
    "CAFE_COMBO",
    "CAFE_FRASE",
    "BEBIDAS_FAMILIAS",
    "TICK",
    "precio_bebida",
    "precio_jarra_min",
]

# ============================================================
#  ORDEN DE IMPRESIÓN (dueño, 2026-07-28) — §6.53
# ============================================================
# Hasta hoy el orden lo daba la posición del dict dentro de SPREADS, así que
# reordenar el menú significaba mover bloques de 200 líneas y el orden real no
# se podía leer en ningún sitio. Ahora vive aquí, en una línea.
#
# Paginación resultante (16 páginas, HERO siempre en página par):
#   p1 portada · p2-3 Bebidas · p4-5 Infantil · p6-7 Entradas ·
#   p8-9 Compartir · p10-11 Típicos · p12-13 De la Calle · p14-15 Postres ·
#   p16 contraportada
# ⚠️ Con 7 pliegos el "pliego libre 2-3" DESAPARECE: ya no hay páginas sueltas
# donde meter la bienvenida o la leyenda-glosario (ver ESTADO.md).
#
# 📌 Desde la Fase 3 el orden lo declara **la carta**, no este archivo: es del
# cliente, igual que sus platillos. El de Parceros vive en
# `secciones/__init__.py`. Aquí solo se recoge.
ORDEN = _carta.ORDEN

# Solo se imprimen los pliegos activos. Un pliego con "activo": False conserva
# aquí todo su contenido pero no se maqueta ni se exporta (ver Brunch).
_POR_SLUG = {s["slug"]: s for s in SPREADS}
_faltan = [s["slug"] for s in SPREADS
           if s.get("activo", True) and s["slug"] not in ORDEN]
if _faltan:
    raise SystemExit(f"⛔ Pliegos activos sin sitio en ORDEN: {', '.join(_faltan)}")
ACTIVOS = [_POR_SLUG[k] for k in ORDEN if _POR_SLUG[k].get("activo", True)]
INACTIVOS = [s["seccion"] for s in SPREADS if not s.get("activo", True)]

# ⚖️ La cuenta de páginas contra el formato. Esto era prosa —«16 páginas,
# múltiplo de 4, HERO siempre en página par»— y la prosa no para un build: al
# pasar de 6 a 7 pliegos hubo que rehacer la cuenta a mano y confiar en que
# nadie se equivocara.
#
# 📌 Ya no se multiplica por 2: **cada arquetipo dice cuántas páginas ocupa**
# (`pliego` 2, `hoja` 1). Suponer que toda hoja son dos páginas era una de las
# cuatro suposiciones que la hoja suelta rompe a la vez.
import formato as _formato

_error = _formato.comprobar_paginas(sum(paginas_de(s) for s in ACTIVOS))
if _error:
    raise SystemExit(_error)

# La hoja va en dos capas desde la Fase 2 del roadmap: la mecánica de página
# —que comparte cualquier menú— y la identidad visual —que cambia con cada
# cliente—. Las genera `herramientas/partir_css.py` desde `menu-v2.css`.
#
# 📌 El orden entre las dos NO decide nada, y eso es una propiedad del corte,
# no una casualidad: la clasificación es por propiedad y global, así que
# ninguna propiedad aparece en los dos archivos y nunca compiten. Se cargan en
# este orden porque se lee mejor, no porque haga falta.
import tema as _tema

CSS = "\n".join((REND / n).read_text(encoding="utf-8")
                for n in ("estructura.css", _tema.ACTIVO.css_piel))
cuerpo = "".join(pagina(s, i) for i, s in enumerate(ACTIVOS))

# 🏷️ El título lo pone la CARTA. Estaba escrito «Parceros Café» aquí: la demo
# generaba un HTML titulado con el nombre de otro restaurante — la misma fuga
# que el lema del pie (Fase 3) y el nombre del PDF de imprenta.
_TITULO = getattr(_carta, "TITULO", {}).get(
    IDIOMA, getattr(_carta, "TITULO", {}).get("es", CARTA))

html = f'''<!DOCTYPE html>
<html lang="{IDIOMA}"><head><meta charset="UTF-8">
<title>{_TITULO}</title>
<link rel="stylesheet" href="style.css">
<style>{CSS}</style>
</head><body>
{cuerpo}
</body></html>'''

SALIDA = idiomas.ruta(REND / "menu-completo.html", IDIOMA)
SALIDA.write_text(html, encoding="utf-8")

# Manifiesto de pliegos activos — lo consume shot_spreads.py para saber
# cuántos PNG exportar y con qué nombre, sin duplicar la lista.
manifiesto = [{"slug": s["slug"], "seccion": s["seccion"],
               "paginas": paginas_de(s)} for s in ACTIVOS]
idiomas.ruta(REND / "spreads-activos.json", IDIOMA).write_text(
    json.dumps(manifiesto, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"{SALIDA.name} generado ·", len(ACTIVOS), "spreads activos ·",
      len(html), f"bytes · idioma {IDIOMA}")
if INACTIVOS:
    print("  ⏸️ desactivados (estructura conservada):", ", ".join(INACTIVOS))
