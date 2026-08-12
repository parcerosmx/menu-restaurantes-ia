#!/usr/bin/env python3
"""Parte `menu-v2.css` en ESTRUCTURA (motor) y PIEL (cliente).

Hermano de `partir_build_menu.py`, y por el mismo motivo: **el reparto lo
genera un script, no una mano.** Si algo está del lado equivocado se ajusta el
MANIFIESTO de aquí y se vuelve a correr. Mover una declaración a mano entre los
dos archivos deja el manifiesto mintiendo.

El problema
-----------
`menu-v2.css` son 2 906 líneas donde estructura y piel están tejidas. Medido:

    566 reglas    38 % solo estructura · 20 % solo piel · **42 % MIXTAS**
    2 036 declaraciones    49 % estructura · 51 % piel

Con un 42 % de reglas mixtas, cortar por regla no sirve: habría que duplicar
238 selectores y decidir a mano, para siempre, en qué mitad va cada línea
nueva. El corte es **por declaración**.

Por qué esto es seguro
----------------------
Podría parecer que partir una hoja de estilo en dos rompe la cascada. No, y la
razón es exacta:

  1. La clasificación es **por propiedad y global**: `color` va SIEMPRE a piel,
     `width` va SIEMPRE a estructura.
  2. Por tanto **ninguna propiedad aparece en los dos archivos** para el mismo
     selector — ni para selectores distintos.
  3. Y como no compiten, **el orden entre los dos archivos no importa**. Solo
     importa el orden DENTRO de cada archivo, y se conserva íntegro.

⚠️ Eso se cae si una propiedad atajo cruza las dos categorías — un `font:` que
fija tamaño (piel) y un `flex:` que fija ancho (estructura) en el mismo bando
contrario. El script **comprueba que no ocurra** y se planta si ocurre.

⚠️ Y lo que esto NO puede ver: partir CSS **no cambia el HTML**, así que
`verificar_split.py` da verde igual. La única red es el diff de PNG.

Uso
---
    python3 render/herramientas/partir_css.py --seco     # qué haría
    python3 render/herramientas/partir_css.py            # escribe los dos
    python3 render/herramientas/partir_css.py --informe  # dónde cae cada cosa
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

# La raíz es la del CLIENTE, no la del paquete: aquí están su HTML, su
# CSS y sus datos. Deducirla de `__file__` daba site-packages.
from ..proyecto import RAIZ as REND

# ⚠️ EL ORDEN DE ESTA LISTA ES EL ORDEN DE LA CASCADA, y no es decorativo.
# En el HTML, `style.css` se enlazaba ANTES que `menu-v2.css`, así que sus
# reglas perdían ante las de aquel a igualdad de especificidad. Si aquí se
# invirtieran, `.badge-seccion` cambiaría de color sin que nadie tocara un
# valor. Se parten en el mismo orden en que se cargaban.
FUENTES = [REND / "archivo" / "style-v1.css", REND / "archivo" / "menu-v2.css"]
# ⚠️ Las dos hojas ya NO están las dos en el mismo sitio: `estructura.css` la
# trae el MOTOR y la piel es del CLIENTE. Buscarlas ambas bajo la raíz del
# proyecto —como se hacía— dejaba la auditoría en «⛔ Falta estructura.css»
# desde que el motor se instala, y una guarda que siempre falla no se lee.
from ..proyecto import css as _css       # noqa: E402
from .. import tema as _tema             # noqa: E402


def _hojas():
    return _css("estructura.css"), _css(_tema.ACTIVO.css_piel)

# ════════════════════════════════════════════════════════════════════════
#  MANIFIESTO — dónde cae cada propiedad
# ════════════════════════════════════════════════════════════════════════
# La pregunta que decide cada línea: **si otro restaurante llega con una
# identidad gráfica totalmente distinta, ¿tocaría esto?**
#   · Sí  → PIEL. Es identidad.
#   · No, pero movería la maqueta → ESTRUCTURA. Es mecánica de página.

ESTRUCTURA = {
    # Caja y flujo
    "display", "position", "top", "left", "right", "bottom", "inset",
    "width", "height", "min-width", "max-width", "min-height", "max-height",
    "overflow", "overflow-x", "overflow-y", "box-sizing", "float", "clear",
    "z-index", "visibility",
    # Espaciado. Discutible —el ritmo de espaciado ES parte de un sistema
    # visual—, pero aquí manda «¿cabe en la página?»: estos números se
    # afinaron contra el alto de la caja, no contra la marca. Un cliente los
    # retoca para que le entren sus productos, no para parecerse a sí mismo.
    "margin", "margin-top", "margin-bottom", "margin-left", "margin-right",
    "padding", "padding-top", "padding-bottom", "padding-left",
    "padding-right", "gap", "row-gap", "column-gap",
    # Flex y grid
    "flex", "flex-direction", "flex-wrap", "flex-grow", "flex-shrink",
    "flex-basis", "align-items", "align-self", "align-content",
    "justify-content", "justify-items", "justify-self", "order",
    "grid-template-columns", "grid-template-rows", "grid-template-areas",
    "grid-column", "grid-row", "grid-area", "grid-auto-flow", "grid-auto-rows",
    "place-items", "place-content", "place-self",
    "columns", "column-count", "column-gap",
    # Impresión. §6.65 vive aquí: sin `break-inside: avoid` el PDF sale
    # distinto de los PNG. Es mecánica de papel, no gusto.
    "break-inside", "break-after", "break-before",
    "page-break-after", "page-break-before", "page-break-inside",
    # Cómo llena una foto su caja: encuadre, no estilo.
    "object-fit", "object-position", "aspect-ratio",
    # Composición de texto que es mecánica, no voz
    "white-space", "list-style", "list-style-type", "vertical-align",
    "word-break", "overflow-wrap", "hyphens", "text-overflow",
    # Mecánica de columna al paginar, hermano de `break-inside`.
    "-webkit-column-break-inside",
    # `size` es de @page: el tamaño del papel. Geometría, y la manda formato.py.
    "size",
    # No pinta nada y en papel no significa nada; es plomería.
    "pointer-events",
}

PIEL = {
    # Color
    "color", "background", "background-color", "background-image",
    "background-size", "background-position", "background-repeat",
    "background-clip", "background-origin", "background-attachment",
    "-webkit-text-fill-color", "-webkit-background-clip", "accent-color",
    # Tipografía. La escala tipográfica es identidad: qué tan grande grita un
    # rótulo frente a su cuerpo es de las cosas que más distinguen una carta.
    "font", "font-family", "font-size", "font-weight", "font-style",
    "font-variant", "font-stretch", "line-height", "letter-spacing",
    "word-spacing", "text-transform", "text-align", "text-decoration",
    "text-decoration-color", "text-decoration-thickness", "text-shadow",
    "text-indent", "font-feature-settings", "text-underline-offset",
    # Forma y adorno. La cinta rasgada, el sello redondo, el giro de 1.4°:
    # esto es la firma de Parceros y nada de ello sobrevive a otra marca.
    "border", "border-top", "border-bottom", "border-left", "border-right",
    "border-color", "border-width", "border-style", "border-radius",
    "border-top-left-radius", "border-top-right-radius",
    "border-bottom-left-radius", "border-bottom-right-radius",
    "box-shadow", "opacity", "transform", "transform-origin", "rotate",
    "scale", "filter", "backdrop-filter", "clip-path", "mask", "mix-blend-mode",
    "content", "outline", "outline-color", "stroke", "fill",
    "border-top-color", "border-bottom-color", "border-left-color",
    "border-right-color",
    # Contorno sobre la letra y en qué orden se pinta. Es puro adorno de
    # rótulo — en la hoja infantil es lo que hace que el título parezca cómic.
    "-webkit-text-stroke", "-webkit-text-stroke-width",
    "-webkit-text-stroke-color", "paint-order",
}

# ⚠️ LOS `@media` SE PARTEN COMO CUALQUIER OTRA REGLA. NO se mandan enteros a
# un lado, y esto costó un pliego para aprenderlo.
#
# El primer intento los metía completos en estructura, «para no partir el
# at-rule». Pero `@media screen { body { background: #6b6b6b } }` lleva dentro
# un `background`, que es de PIEL. Al mandarlo entero a estructura, esa
# declaración pasó a cargarse ANTES que el `html, body { background: #fff }` de
# `style.css` —que sí había ido a piel— y el blanco ganó: el fondo gris de la
# previsualización desapareció, y con él la fila y=0 de los PNG.
#
# Es exactamente la propiedad de seguridad de la cabecera rompiéndose: en
# cuanto una propiedad puede estar en los dos archivos, el orden entre ellos
# vuelve a decidir. La excepción cómoda era la única grieta del corte.
#
# Lo cazó el diff de PNG y nada más: 2 902 píxeles de una fila, el 0.046 % de
# la imagen. No lo habría visto nadie mirando.


# ════════════════════════════════════════════════════════════════════════
#  Analizador
# ════════════════════════════════════════════════════════════════════════
def trocear(css):
    """Devuelve una lista de trozos: comentarios, at-rules y reglas.

    Escáner con recuento de llaves que respeta comentarios y cadenas. No es un
    parser de CSS completo y no pretende serlo: cubre exactamente lo que hay en
    este archivo, y se planta si encuentra algo que no sabe leer.
    """
    trozos, i, n = [], 0, len(css)
    pend = ""                      # comentario pendiente de pegar a su regla
    while i < n:
        # Comentario
        if css.startswith("/*", i):
            j = css.index("*/", i) + 2
            pend += css[i:j]
            # el salto de línea que sigue pertenece al comentario
            while j < n and css[j] == "\n":
                pend += "\n"
                j += 1
            i = j
            continue
        # Espacio suelto
        if css[i].isspace():
            pend += css[i]
            i += 1
            continue
        # Regla o at-rule: leer hasta `{` y luego casar llaves
        j = i
        while j < n and css[j] != "{":
            if css[j] == ";" and css.startswith("@", i):
                break            # at-rule sin cuerpo (@import, @charset)
            j += 1
        if j >= n:
            raise SystemExit(f"⛔ No sé leer el CSS desde el byte {i}.")
        selector = css[i:j].strip()
        if css[j] == ";":
            trozos.append(("crudo", pend + css[i:j + 1]))
            pend, i = "", j + 1
            continue
        prof, k = 0, j
        while k < n:
            c = css[k]
            if c == "'" or c == '"':
                cierre = c
                k += 1
                while k < n and css[k] != cierre:
                    k += 1
            elif css.startswith("/*", k):
                k = css.index("*/", k) + 1
            elif c == "{":
                prof += 1
            elif c == "}":
                prof -= 1
                if prof == 0:
                    break
            k += 1
        cuerpo = css[j + 1:k]
        if selector.startswith("@"):
            # Con cuerpo de REGLAS (@media, @supports) se recursa: hay que
            # partirlo igual que todo lo demás. Sin él (@page, @font-face) el
            # cuerpo son declaraciones sueltas y se trata como una regla más.
            if re.search(r"\{", cuerpo):
                trozos.append(("atrule", pend, selector, cuerpo))
            else:
                trozos.append(("regla", pend, selector, cuerpo))
        else:
            trozos.append(("regla", pend, selector, cuerpo))
        pend, i = "", k + 1
    if pend.strip():
        trozos.append(("crudo", pend))
    return trozos


def declaraciones(cuerpo):
    """Parte el cuerpo de una regla en (comentario, propiedad, valor-crudo).

    Respeta cadenas y paréntesis: `url('data:…;utf8,…')` lleva un `;` dentro y
    `clip-path: polygon(…, …)` lleva comas — ninguno de los dos separa.
    """
    out, i, n, pend = [], 0, len(cuerpo), ""
    while i < n:
        if cuerpo.startswith("/*", i):
            j = cuerpo.index("*/", i) + 2
            pend += cuerpo[i:j]
            i = j
            continue
        if cuerpo[i].isspace():
            pend += cuerpo[i]
            i += 1
            continue
        j, par = i, 0
        while j < n:
            c = cuerpo[j]
            if c in "'\"":
                cierre = c
                j += 1
                while j < n and cuerpo[j] != cierre:
                    j += 1
            elif c == "(":
                par += 1
            elif c == ")":
                par -= 1
            elif c == ";" and par == 0:
                break
            j += 1
        texto = cuerpo[i:j].strip()
        if texto:
            m = re.match(r"([-a-zA-Z]+)\s*:\s*(.*)", texto, re.S)
            if not m:
                raise SystemExit(f"⛔ Declaración que no sé leer: «{texto[:60]}»")
            out.append((pend, m.group(1), m.group(2)))
        pend, i = "", j + 1
    return out, pend


def lado(prop):
    if prop.startswith("--"):
        # Las variables locales de una regla (p.ej. `--fondo` en `.page`) son
        # valores de color: piel.
        return "P"
    if prop in ESTRUCTURA:
        return "E"
    if prop in PIEL:
        return "P"
    return None


# ════════════════════════════════════════════════════════════════════════
def partir(css):
    trozos = trocear(css)
    est, pie = [], []
    desconocidas = Counter()
    n_e = n_p = n_mixtas = 0

    for tr in trozos:
        if tr[0] == "crudo":
            est.append(tr[1]); pie.append(tr[1])
            continue
        if tr[0] == "atrule":
            _, comentario, selector, cuerpo = tr
            sub_e, sub_p, sub_d, sub_n = partir(cuerpo)
            desconocidas.update(sub_d)
            n_e += sub_n[0]; n_p += sub_n[1]; n_mixtas += sub_n[2]
            if sub_e.strip():
                est.append(f"{comentario}{selector} {{\n{sub_e}}}\n")
            if sub_p.strip():
                pie.append(f"{comentario if not sub_e.strip() else ''}"
                           f"{selector} {{\n{sub_p}}}\n")
            continue
        _, comentario, selector, cuerpo = tr
        decls, cola = declaraciones(cuerpo)
        de, dp = [], []
        for pre, prop, val in decls:
            l = lado(prop)
            if l is None:
                desconocidas[prop] += 1
                l = "P"        # sin clasificar → piel, que es lo conservador
            (de if l == "E" else dp).append((pre, prop, val))

        if de and dp:
            n_mixtas += 1
        elif de:
            n_e += 1
        elif dp:
            n_p += 1

        # El comentario viaja con el lado que recibe MÁS declaraciones. En
        # empate va a piel: casi todos explican una decisión visual.
        com_e = comentario if len(de) > len(dp) else ""
        com_p = comentario if len(dp) >= len(de) else ""

        if de:
            est.append(_regla(com_e, selector, de, cola if not dp else ""))
        if dp:
            pie.append(_regla(com_p, selector, dp, cola))

    return "".join(est), "".join(pie), desconocidas, (n_e, n_p, n_mixtas)


def _regla(comentario, selector, decls, cola):
    cuerpo = ""
    for pre, prop, val in decls:
        cuerpo += pre if pre else ""
        cuerpo += f"{prop}: {val};"
    cuerpo += cola
    if not cuerpo.strip().startswith(("\n", " ")):
        cuerpo = "\n  " + cuerpo.lstrip()
    return f"{comentario}{selector} {{{cuerpo}}}\n"


def comprobar_atajos():
    """Ningún atajo puede cruzar las dos categorías. Ver la cabecera."""
    ATAJOS = {
        "font": {"font-family", "font-size", "font-weight", "font-style",
                 "line-height", "font-variant"},
        "background": {"background-color", "background-image",
                       "background-position", "background-size",
                       "background-repeat"},
        "border": {"border-color", "border-width", "border-style"},
        "flex": {"flex-grow", "flex-shrink", "flex-basis"},
        "margin": {"margin-top", "margin-bottom", "margin-left", "margin-right"},
        "padding": {"padding-top", "padding-bottom", "padding-left",
                    "padding-right"},
    }
    malos = []
    for atajo, largas in ATAJOS.items():
        la = lado(atajo)
        for larga in largas:
            ll = lado(larga)
            if ll is not None and la is not None and ll != la:
                malos.append(f"{atajo} ({la}) ≠ {larga} ({ll})")
    if malos:
        raise SystemExit("⛔ Un atajo cruza las dos categorías; la cascada "
                         "dejaría de ser segura:\n  " + "\n  ".join(malos))


def auditar():
    """¿Sigue cada declaración del lado que le toca?

    Desde que `estructura.css` y `piel-parceros.css` son la FUENTE, el corte ya
    no se rehace: se comprueba. Volver a partir borraría lo que se haya escrito
    a mano desde entonces, que es justo lo que no queremos.

    Esto es el equivalente de `verificar_split.py` para el CSS, con una
    diferencia que importa: aquel compara el HTML byte a byte, y **el CSS no
    cambia el HTML**. Aquí lo único que se puede afirmar es que cada
    declaración está donde el manifiesto dice.
    """
    comprobar_atajos()
    problemas, desconocidas = [], Counter()
    est, piel = _hojas()
    for ruta, esperado, etiqueta in ((est, "E", "estructura"),
                                     (piel, "P", "piel")):
        for tr in trocear(ruta.read_text(encoding="utf-8")):
            if tr[0] != "regla":
                continue
            _, _, selector, cuerpo = tr
            decls, _ = declaraciones(cuerpo)
            for _, prop, _v in decls:
                l = lado(prop)
                if l is None:
                    desconocidas[prop] += 1
                elif l != esperado:
                    otro = "piel" if esperado == "E" else "estructura"
                    problemas.append(
                        f"  {ruta.name}  «{selector.strip()[:44]}»  "
                        f"`{prop}` es de {otro}")

    if desconocidas:
        print(f"⚠️ {len(desconocidas)} propiedades no están en el MANIFIESTO:")
        for p, n in desconocidas.most_common():
            print(f"     {n:>3}  {p}")
    if problemas:
        print(f"\n⛔ {len(problemas)} declaraciones del lado equivocado:")
        for p in problemas[:30]:
            print(p)
        if len(problemas) > 30:
            print(f"  … y {len(problemas) - 30} más")
        print("\n   O se mueven a su archivo, o se cambia el MANIFIESTO —")
        print("   pero con un motivo, no para que deje de avisar.")
        return 1
    if desconocidas:
        return 1
    print("✅ Cada declaración está del lado que dice el manifiesto.")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seco", action="store_true", help="no escribe nada")
    ap.add_argument("--informe", action="store_true",
                    help="enseña las propiedades sin clasificar")
    ap.add_argument("--auditar", action="store_true",
                    help="comprueba los dos archivos VIGENTES sin regenerarlos")
    args = ap.parse_args()

    if args.auditar:
        return auditar()

    faltan = [f for f in FUENTES if not f.exists()]
    if faltan:
        raise SystemExit(
            "⛔ No están las fuentes del corte: "
            + ", ".join(f.name for f in faltan) + "\n"
            "   `estructura.css` y `piel-parceros.css` son ya la FUENTE; esto\n"
            "   solo sirve para rehacer el corte desde cero.\n"
            "   Para comprobar el reparto vigente:  --auditar")

    comprobar_atajos()
    css = "\n".join(f.read_text(encoding="utf-8") for f in FUENTES)
    est, pie, desconocidas, (n_e, n_p, n_mix) = partir(css)

    for f in FUENTES:
        print(f"  fuente     {f.name:<22} {len(f.read_bytes()):>7} bytes")
    print(f"  estructura {'estructura.css':<22} {len(est):>7} bytes")
    print(f"  piel       {'piel-parceros.css':<22} {len(pie):>7} bytes")
    print(f"\n  reglas: {n_e} solo estructura · {n_p} solo piel · {n_mix} partidas")

    if desconocidas:
        print(f"\n  ⚠️ {len(desconocidas)} propiedades SIN CLASIFICAR "
              "(han ido a piel por prudencia):")
        for p, n in desconocidas.most_common():
            print(f"       {n:>3}  {p}")
        print("     Decídelas en el MANIFIESTO y vuelve a correr.")

    if args.seco:
        print("\n(--seco: no se ha escrito nada)")
        return 0

    cab = ("/* ═══════════════════════════════════════════════════════════\n"
           "   {0}\n"
           "   ⚠️ GENERADO por herramientas/partir_css.py — no editar a mano.\n"
           "   El reparto se ajusta en el MANIFIESTO de ese script.\n"
           "   ═══════════════════════════════════════════════════════════ */\n\n")
    (REND / 'estructura.css').write_text(cab.format(
        "ESTRUCTURA — mecánica de página. La comparte cualquier menú.") + est,
        encoding="utf-8")
    (REND / 'piel-parceros.css').write_text(cab.format(
        "PIEL «parceros» — identidad visual. Cambia con cada cliente.") + pie,
        encoding="utf-8")
    print(f"\n✅ escritos.  ⚠️ Partir CSS no cambia el HTML: la única red es el "
          "diff de PNG.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
