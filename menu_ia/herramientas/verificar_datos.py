#!/usr/bin/env python3
"""Comprueba que el menú no imprime una mentira. Corre en cada build.

Qué vigila y por qué
--------------------
Un menú impreso es una promesa que dura todo el tiraje. Los errores que se
pagan caros no son de maquetación —esos se ven— sino de DATO: una foto que no
carga y sale un hueco, el mismo plato a dos precios en dos páginas, un precio
que se quedó vacío. Todos son invisibles en pantalla hasta que ya están en
papel.

Esta guarda existe porque los tres han pasado ya en este proyecto:

  · Tres fotos del menú no existían en disco y el render **no dijo nada**:
    salieron tres huecos y solo se vio comparando el peso de los PNG.
  · `datos/menu-items.json` decía Chuleta Valluna 230 cuando el menú imprimía
    240, porque nadie regeneró el volcado tras subir el precio.
  · El Chocolate se imprime en dos hojas (Bebidas y Postres) desde una lista
    única — justo para que no pueda haber dos precios. Sin comprobarlo, esa
    garantía es una intención.

🔴 son errores: paran el build. 🟡 son avisos: se listan y se sigue, porque
§6.5 permite productos marcados como pendientes a propósito.

Uso
---
    python3 render/herramientas/verificar_datos.py
    python3 render/herramientas/verificar_datos.py --estricto   # 🟡 también fallan
"""
import argparse
import collections
import importlib.util
import io
import json
import re
import sys
from contextlib import redirect_stdout
from dataclasses import asdict
from pathlib import Path

# La raíz es la del CLIENTE, no la del paquete: aquí están su HTML, su
# CSS y sus datos. Deducirla de `__file__` daba site-packages.
from ..proyecto import RAIZ as REND
RAIZ = REND.parent
sys.path.insert(0, str(REND))

from ..motor import enganches as _eng  # noqa: E402


class _Item:
    """La forma mínima que espera el resto de la guarda.

    El recorrido genérico devolvía diccionarios y el resto lee atributos
    (`i.precio`, `i.modificador`): reventaba tres funciones más abajo con un
    `AttributeError` que no menciona ni al recorrido ni a la carta.
    """
    __slots__ = ("nombre", "precio", "hoja", "foto", "clave",
                 "modificador", "sub", "costeable", "receta_id")

    def __init__(self, nombre, precio, hoja, foto):
        self.nombre, self.precio, self.hoja, self.foto = nombre, precio, hoja, foto
        self.clave = f"{hoja}/{nombre}"
        self.modificador = self.sub = self.costeable = False
        self.receta_id = None


def cargar_items():
    """Lista plana de precios, recorrida del render VIVO — no del volcado.

    Leer `datos/menu-items.json` sería más rápido y estaría mal: ese archivo es
    una copia que puede estar vieja, y comprobar el menú contra una copia vieja
    es exactamente el fallo que esta guarda busca."""
    with redirect_stdout(io.StringIO()):     # build_menu imprime su progreso
        # ⚠️ El import va PRIMERO, y no es cosmético: importar `build_menu`
        # importa la carta, y es la carta la que REGISTRA su recorrido. Al
        # revés se preguntaba por un enganche que todavía no existía y siempre
        # caía al genérico — con el agravante de que el genérico devolvía otra
        # forma de dato y reventaba tres funciones más abajo.
        from .. import build_menu as bm
        propio = _eng.items_planos()
        if propio is not None:
            return propio
        # Recorrido genérico: sirve a cualquier carta con la forma mínima
        # —hojas con `items` que tienen nombre y precio—. Un proyecto con
        # zonas propias registra el suyo y saca más.
        #
        # ⚠️ Esto era `import items_menu`, un módulo de UN cliente. El motor
        # exigía que todo proyecto tuviera un archivo con ese nombre, y sin él
        # su guarda de datos moría con ModuleNotFoundError. Se vio instalando
        # en una máquina limpia y corriendo el ejemplo de este mismo repo.
        fuera = []
        for hoja in bm.ACTIVOS:
            for it in hoja.get("items", []):
                if not it.get("activo", True):
                    continue
                fuera.append(_Item(it.get("n", ""), it.get("precio", ""),
                                   hoja.get("seccion", ""), it.get("foto", "")))
            h = hoja.get("hero") or {}
            if h.get("nombre"):
                fuera.append(_Item(h["nombre"].replace("|", " "),
                                   h.get("precio", ""), hoja.get("seccion", ""),
                                   h.get("foto", "")))
        return fuera


# ── 🔴 Errores ───────────────────────────────────────────────────────────────

def fotos_que_faltan():
    """Imágenes referenciadas por el HTML que no están en disco.

    Chromium no protesta por un `src` roto: pinta el hueco y sigue. Por eso
    esto tiene que comprobarlo alguien."""
    html = (REND / "menu-completo.html").read_text(encoding="utf-8")
    refs = set(re.findall(r'src="([^"]+)"', html))
    refs |= set(re.findall(r'url\(&quot;([^&]+)&quot;\)', html))
    faltan = []
    for r in sorted(refs):
        if r.startswith(("data:", "http", "#")):
            continue
        if not (REND / r).resolve().exists():
            faltan.append(r)
    return [f"foto que no existe en disco: {r}" for r in faltan]


def precios_contradictorios(items):
    """El mismo producto impreso a dos precios distintos.

    Los modificadores se excluyen: una adición puede valer distinto según el
    plato al que se le pega, y eso es una decisión, no un error."""
    por_nombre = collections.defaultdict(set)
    for i in items:
        if i.precio and not i.modificador:
            por_nombre[i.nombre.strip().lower()].add(i.precio)
    return [f"«{n}» se imprime a {' y a '.join(sorted(p))} en páginas distintas"
            for n, p in sorted(por_nombre.items()) if len(p) > 1]


# §6.2: el precio va sin `$` y sin separador de miles. Dos formas válidas:
#   «230»       un precio
#   «65 / 230»  dos, que es como la carta de bebidas imprime vaso/jarra y
#               trago/botella. El segundo puede ser «—» cuando esa medida no
#               se vende (limonada de aguacate: hay vaso, no hay jarra).
PRECIO_OK = re.compile(r"\d+(\s*/\s*(\d+|—))?")


def precios_mal_escritos(items):
    return [f"precio mal escrito en {i.clave}: {i.precio!r} "
            f"(§6.2: dígitos, o «65 / 230» para vaso/jarra — nunca `$`)"
            for i in items
            if i.precio and not PRECIO_OK.fullmatch(i.precio.strip())]


# ── 🟡 Avisos ────────────────────────────────────────────────────────────────

def sin_precio(items):
    """Productos sin precio. §6.5 los permite marcados como pendientes, pero
    hay que verlos: un pendiente que llega a la plancha es un hueco."""
    return [f"sin precio: {i.clave}" for i in items
            if i.costeable and not i.sub and not i.precio]


def volcado_desincronizado(items):
    """`datos/menu-items.json` contra lo que el render dice ahora."""
    destino = RAIZ / "datos" / "menu-items.json"
    if not destino.exists():
        return ["datos/menu-items.json no existe · córrelo con items_menu.py"]
    viejo = json.loads(destino.read_text(encoding="utf-8"))
    nuevo = [asdict(i) for i in items]
    if viejo == nuevo:
        return []
    idx = {i["clave"]: i for i in viejo}
    difs = []
    for n in nuevo:
        v = idx.get(n["clave"])
        if v is None:
            difs.append(f"  · {n['clave']} es nuevo en el render")
        elif v.get("precio") != n["precio"]:
            difs.append(f"  · {n['clave']}: volcado {v.get('precio')!r} "
                        f"≠ menú {n['precio']!r}")
    faltantes = [c for c in idx if c not in {n["clave"] for n in nuevo}]
    difs += [f"  · {c} ya no está en el menú" for c in faltantes[:5]]
    return ([f"datos/menu-items.json está viejo ({len(difs)} diferencias) · "
             f"regenéralo con `python3 render/items_menu.py`"] + difs[:12])


def sin_receta(items):
    cost = [i for i in items if i.costeable]
    huerf = [i for i in cost if not i.receta_id]
    if not huerf:
        return []
    return [f"{len(huerf)} de {len(cost)} líneas costeables no están vinculadas "
            f"a una receta · no se les puede calcular el CMV"]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--estricto", action="store_true",
                    help="los avisos 🟡 también hacen fallar el build")
    args = ap.parse_args()

    items = cargar_items()

    errores = (fotos_que_faltan()
               + precios_contradictorios(items)
               + precios_mal_escritos(items))
    avisos = sin_precio(items) + volcado_desincronizado(items) + sin_receta(items)

    print(f"🔎 {len(items)} líneas de precio comprobadas")

    for a in avisos:
        print(f"  🟡 {a}" if not a.startswith("  ") else a)
    for e in errores:
        print(f"  🔴 {e}")

    if errores:
        print(f"\n⛔ {len(errores)} error(es) de dato. El menú imprimiría algo "
              f"que no es verdad.")
        return 1
    if avisos and args.estricto:
        print(f"\n⛔ {len(avisos)} aviso(s), y --estricto los cuenta como error.")
        return 1
    print("✅ Sin errores de dato." + (f" ({len(avisos)} aviso/s)" if avisos else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
