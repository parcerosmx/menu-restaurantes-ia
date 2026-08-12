#!/usr/bin/env python3
"""El formato físico de la pieza: cuánto mide, cuánto sangra y cómo se encuaderna.

Por qué existe
--------------
Hasta hoy la geometría del menú vivía en **seis sitios a la vez**, con los
mismos números tecleados en cada uno:

    style.css                  --page-w: 192mm  --page-h: 285mm  --bleed: 3mm
    build_pdf_plano.py         PAGINA_MM = (192, 285)   SANGRADO_MM = 3
    preparar_pdf_imprenta.py   CORTE_MM = (186.0, 279.0)  SANGRADO_MM = 3.0
    imponer_pdf.py             PAGINA_FINAL_MM = (186, 279)  SANGRE_MM = 3
    comparar_geometria.py      384.0 (el ancho del pliego)  192.0 (el lado)
    build_tapas_final.py       "@page { size: 192mm 285mm }"  dos veces

Seis copias de un dato que **tiene que ser el mismo o el archivo no imprime**.
Y no era un riesgo teórico: cambiar de formato exigía acertar en los seis, y
equivocarse en uno solo no da error — da un PDF cuyo `TrimBox` no coincide con
lo que dibujó Chromium, que es exactamente el fallo que solo se ve en la
plancha.

Aquí el dato está una vez. Lo demás lo lee.

⚠️ **Esto NO es maquetación.** Dice cuánto mide el papel y cómo se dobla, no
qué se dibuja encima. La estructura de la página (pliego con hero + listado,
hoja suelta, …) es otra cosa y llega en la Fase 3 del roadmap.

Uso
---
    python3 render/formato.py              # enseña el formato activo
    python3 render/formato.py --aplicar    # sincroniza el bloque de style.css
    python3 render/formato.py --verificar  # ¿style.css concuerda? (lo usa el build)

    MENU_FORMATO=a4-hoja python3 render/formato.py
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

# La raíz es la del CLIENTE (ahí está su style.css), no la del paquete.
from .proyecto import RAIZ as REND

# Los dos centinelas que acotan el bloque generado dentro de `style.css`.
# Mismo recurso que usa `herramientas/sanear_estado.py`: sin una marca
# explícita, una segunda pasada no sabe qué escribió la anterior.
INI = "  /* ⇩⇩ GENERADO POR render/formato.py — no editar a mano ⇩⇩ */"
FIN = "  /* ⇧⇧ fin del bloque generado ⇧⇧ */"


def _mm(v):
    """`192` → `"192"`, `4.5` → `"4.5"`. Sin `.0` colgando en el CSS."""
    return f"{v:g}"


class Formato:
    """Un formato de pieza impresa.

    El dato canónico es **el corte** —lo que mide la página ya guillotinada— y
    el sangrado. Todo lo demás se deriva: la página con sangre es el corte más
    dos sangrados, y esa es la caja que Chromium tiene que dibujar.
    """

    def __init__(self, nombre, corte_mm, sangrado_mm, margen_exterior_mm,
                 encuadernacion, paginas, marca_mm=10, largo_marca_mm=5,
                 paginas_tapas=2, nota=""):
        self.nombre = nombre
        self.corte_mm = tuple(corte_mm)
        self.sangrado_mm = sangrado_mm
        self.margen_exterior_mm = margen_exterior_mm
        self.encuadernacion = encuadernacion
        self.paginas = paginas
        self.marca_mm = marca_mm
        self.largo_marca_mm = largo_marca_mm
        # Cuántas de esas páginas son tapa. En el cuadernillo son 2 —portada y
        # contraportada, que viven en su propio HTML—; una hoja suelta no tiene.
        self.paginas_tapas = paginas_tapas
        self.nota = nota
        self.validar()

    @property
    def paginas_contenido(self):
        return self.paginas - self.paginas_tapas

    def comprobar_paginas(self, contenido):
        """¿Cabe este contenido en el formato? Devuelve el error o None.

        Lo llama `build_menu.py` con las páginas que de verdad ha maquetado.
        Antes esto era un comentario —«16 páginas, múltiplo de 4, la cara
        izquierda del pliego siempre en página par»— y un comentario no para
        un build: el 2026-07-28 se pasó de 6 a 7 pliegos y la cuenta se rehízo
        a mano.
        """
        if contenido == self.paginas_contenido:
            return None
        return (
            f"⛔ El contenido son {contenido} páginas y el formato "
            f"«{self.nombre}» declara {self.paginas_contenido} "
            f"({self.paginas} totales − {self.paginas_tapas} de tapa).\n"
            f"   Encuadernación «{self.encuadernacion}».\n"
            f"   O sobra/falta contenido, o hay que cambiar `paginas` en "
            f"render/formato.py — y entonces tiene que seguir cumpliendo la "
            f"regla de la encuadernación.")

    # ── Derivados ───────────────────────────────────────────────────────
    @property
    def pagina_mm(self):
        """La caja que se dibuja: el corte más sangre por los cuatro lados."""
        w, h = self.corte_mm
        return (w + 2 * self.sangrado_mm, h + 2 * self.sangrado_mm)

    @property
    def pliego_mm(self):
        """Dos páginas enfrentadas. En `hoja` no existe: devuelve la página."""
        w, h = self.pagina_mm
        return (w * 2, h) if self.encuadernacion == "grapa" else (w, h)

    # ── Reglas de encuadernación ────────────────────────────────────────
    # Esto vivía en prosa dentro de `build_menu.py` («16 páginas, múltiplo de
    # 4, la cara izquierda del pliego siempre en página par»). Un comentario no
    # para un build; esto sí.
    REGLAS = {
        # Grapa (saddle stitch): el cuadernillo se forma con hojas dobladas por
        # la mitad, así que cada hoja aporta 4 páginas. Un número que no sea
        # múltiplo de 4 no se puede encuadernar — no es una preferencia.
        "grapa": lambda n: n >= 4 and n % 4 == 0,
        # Hoja suelta: una cara o dos. Sin doblez y sin grapa.
        "hoja": lambda n: n in (1, 2),
    }

    def validar(self):
        if self.encuadernacion not in self.REGLAS:
            raise ValueError(
                f"⛔ Encuadernación desconocida: «{self.encuadernacion}». "
                f"Conocidas: {', '.join(self.REGLAS)}")
        if not self.REGLAS[self.encuadernacion](self.paginas):
            explica = {
                "grapa": "la grapa dobla hojas por la mitad: cada hoja son 4 "
                         "páginas, así que el total tiene que ser múltiplo de 4",
                "hoja": "una hoja suelta tiene una cara o dos, no más",
            }[self.encuadernacion]
            raise ValueError(
                f"⛔ {self.paginas} páginas no se pueden encuadernar a "
                f"«{self.encuadernacion}»: {explica}.")

    # ── Salidas ─────────────────────────────────────────────────────────
    def bloque_css(self):
        w, h = self.pagina_mm
        cw, ch = self.corte_mm
        return "\n".join([
            INI,
            f"  /* Formato «{self.nombre}» · {self.encuadernacion} · "
            f"{self.paginas} páginas.",
            f"     Página final {_mm(cw)}×{_mm(ch)}mm; "
            f"+{_mm(self.sangrado_mm)}mm de bleed por lado → "
            f"{_mm(w)}×{_mm(h)}mm.",
            "     El dato vive en render/formato.py y se aplica con",
            "     `python3 render/formato.py --aplicar`. */",
            f"  --page-w: {_mm(w)}mm;",
            f"  --page-h: {_mm(h)}mm;",
            f"  --bleed: {_mm(self.sangrado_mm)}mm;",
            f"  --margen-exterior: {_mm(self.margen_exterior_mm)}mm;",
            FIN,
        ])

    def __str__(self):
        w, h = self.pagina_mm
        cw, ch = self.corte_mm
        return (f"{self.nombre} · {self.encuadernacion} · {self.paginas} págs\n"
                f"  corte    {_mm(cw)} × {_mm(ch)} mm\n"
                f"  con sangre {_mm(w)} × {_mm(h)} mm  (bleed {_mm(self.sangrado_mm)} mm)\n"
                f"  margen exterior {_mm(self.margen_exterior_mm)} mm"
                + (f"\n  {self.nota}" if self.nota else ""))


# ════════════════════════════════════════════════════════════════════════
#  Los formatos que conoce el proyecto
# ════════════════════════════════════════════════════════════════════════
FORMATOS = {
    # El de Parceros. Los números NO se han tocado al extraerlos: son los que
    # llevan siete pliegos hasta la plancha, y ese es el único aval que vale.
    "cuadernillo-esbelto": Formato(
        nombre="cuadernillo-esbelto",
        corte_mm=(186, 279),
        sangrado_mm=3,
        margen_exterior_mm=13,
        encuadernacion="grapa",
        paginas=16,
        nota="Carta recortada 1.5 cm por lado. Probado hasta la plancha.",
    ),
    # Prueba de la Fase 1: MISMO contenido, OTRA caja. Existe para demostrar
    # que la geometría se propaga de verdad —CSS, PNG, PDF, cajas del archivo
    # de imprenta— y no solo en el módulo que la declara.
    # ⚠️ Sale FEO a propósito: la maqueta está afinada para 186 × 279 y aquí
    # tiene 24 mm más de ancho. Lo que prueba es que el parámetro manda, no que
    # el diseño aguante. Que aguante es la Fase 3.
    "a4-cuadernillo": Formato(
        nombre="a4-cuadernillo",
        corte_mm=(210, 297),
        sangrado_mm=3,
        margen_exterior_mm=13,
        encuadernacion="grapa",
        paginas=16,
        nota="⚠️ Prueba del motor. La maqueta no está afinada para esta caja.",
    ),
    # A4 a doble cara, sin encuadernar. Hoy NO se puede maquetar —el contenido
    # de Parceros son 14 páginas y aquí caben 2—, y eso es correcto: el
    # arquetipo de hoja suelta llega en la Fase 3. Está aquí porque es lo que
    # hace que la regla de encuadernación tenga algo contra qué fallar.
    # ⚠️ NO está probado en plancha. `style-guide.md` §9.5-ter: un archivo de
    # imprenta no se da por bueno hasta abrirlo en Illustrator, y este no ha
    # pasado por ahí. Sirve para verificar el motor, no para mandar al taller.
    "a4-hoja": Formato(
        nombre="a4-hoja",
        corte_mm=(210, 297),
        sangrado_mm=3,
        margen_exterior_mm=12,
        encuadernacion="hoja",
        paginas=2,
        paginas_tapas=0,      # una hoja suelta no tiene tapas
        nota="⚠️ Sin prueba de plancha. Verifica el motor, no se manda al taller.",
    ),
}

# El formato activo. `MENU_FORMATO` permite probar otro sin tocar el código —
# que es justo lo que necesita la prueba de salida de la Fase 1.
# Alias heredados. El formato se llamaba por el cliente que lo estrenó, y en
# un motor que sirve a cualquiera eso no se sostiene: `cuadernillo-esbelto`
# dice qué es —carta recortada, 16 páginas, grapa— sin nombrar a nadie.
# El alias se conserva para no romper una configuración existente.
ALIAS = {"parceros-cuadernillo": "cuadernillo-esbelto"}

NOMBRE_ACTIVO = os.environ.get("MENU_FORMATO", "cuadernillo-esbelto")
NOMBRE_ACTIVO = ALIAS.get(NOMBRE_ACTIVO, NOMBRE_ACTIVO)
if NOMBRE_ACTIVO not in FORMATOS:
    raise SystemExit(
        f"⛔ MENU_FORMATO=«{NOMBRE_ACTIVO}» no existe. "
        f"Conocidos: {', '.join(FORMATOS)}")

ACTIVO = FORMATOS[NOMBRE_ACTIVO]

# ── Superficie que consumen los scripts ─────────────────────────────────
# Se exponen con los MISMOS nombres que tenían donde estaban, para que el
# cambio en cada script sea sustituir la constante por un import y nada más.
CORTE_MM = ACTIVO.corte_mm
PAGINA_MM = ACTIVO.pagina_mm
SANGRADO_MM = ACTIVO.sangrado_mm
MARGEN_EXTERIOR_MM = ACTIVO.margen_exterior_mm
MARCA_MM = ACTIVO.marca_mm
LARGO_MARCA_MM = ACTIVO.largo_marca_mm
PAGINAS = ACTIVO.paginas
PAGINAS_CONTENIDO = ACTIVO.paginas_contenido
ENCUADERNACION = ACTIVO.encuadernacion
comprobar_paginas = ACTIVO.comprobar_paginas


# ════════════════════════════════════════════════════════════════════════
#  Sincronización con style.css
# ════════════════════════════════════════════════════════════════════════
# `style.css` no se genera entero: es una hoja escrita a mano con su paleta y
# sus tipografías. Solo se genera **el bloque de geometría**, acotado entre los
# dos centinelas.
#
# 📌 Y el build **verifica, no arregla**. Es la regla del proyecto: las guardas
# paran (`verificar_datos.py`), no corrigen en silencio. Un script que reescribe
# un archivo rastreado a tus espaldas convierte un `git diff` en ruido.
def _style():
    return REND / "style.css"


def bloque_actual(texto=None):
    texto = _style().read_text(encoding="utf-8") if texto is None else texto
    m = re.search(re.escape(INI) + r".*?" + re.escape(FIN), texto, re.S)
    return m.group(0) if m else None


def aplicar():
    ruta = _style()
    texto = ruta.read_text(encoding="utf-8")
    nuevo = ACTIVO.bloque_css()
    actual = bloque_actual(texto)
    if actual is None:
        raise SystemExit(
            "⛔ No encuentro el bloque generado en style.css.\n"
            f"   Tiene que existir un bloque entre:\n     {INI}\n     {FIN}")
    if actual == nuevo:
        print(f"✅ style.css ya concuerda con «{ACTIVO.nombre}».")
        return 0
    ruta.write_text(texto.replace(actual, nuevo), encoding="utf-8")
    print(f"✅ style.css sincronizado con «{ACTIVO.nombre}».")
    return 0


def verificar():
    """0 si concuerda, 1 si no. Lo llama el build antes de maquetar."""
    actual = bloque_actual()
    if actual is None:
        print("⛔ style.css no tiene el bloque de geometría generado.")
        return 1
    if actual != ACTIVO.bloque_css():
        print(f"⛔ style.css NO concuerda con el formato «{ACTIVO.nombre}».\n"
              "   Chromium maquetaría con una caja y el PDF declararía otra: el\n"
              "   TrimBox no cuadraría con lo dibujado, y eso solo se ve en la\n"
              "   plancha.\n"
              "   Arréglalo con:  python3 render/formato.py --aplicar")
        return 1
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aplicar", action="store_true",
                    help="escribe el bloque de geometría en style.css")
    ap.add_argument("--verificar", action="store_true",
                    help="falla si style.css no concuerda con el formato activo")
    args = ap.parse_args()

    if args.aplicar:
        return aplicar()
    if args.verificar:
        r = verificar()
        if r == 0:
            print(f"✅ style.css concuerda con «{ACTIVO.nombre}».")
        return r

    print(ACTIVO)
    print(f"\n  pliego   {' × '.join(_mm(v) for v in ACTIVO.pliego_mm)} mm")
    print(f"\nFormatos conocidos: {', '.join(FORMATOS)}")
    print("Cambiar:  MENU_FORMATO=<nombre> python3 render/hacer.py menu")
    return 0


if __name__ == "__main__":
    sys.exit(main())
