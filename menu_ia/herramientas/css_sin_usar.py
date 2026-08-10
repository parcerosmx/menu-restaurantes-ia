#!/usr/bin/env python3
"""Encuentra —y opcionalmente poda— reglas CSS que ningún HTML vivo usa.

Por qué con tanto cuidado
-------------------------
`menu-v2.css` tiene 2 931 líneas y 309 clases; los HTML vivos usan 242. Las 67
restantes **no son todas basura**, y ahí está el riesgo: la mitad son rutas de
render vivas que las 7 hojas actuales no ejercitan —`zona_feat`, `zona_flujo`,
los placeholders `.pend` / `.ph` que §6.5 manda usar para lo que aún no existe.
Borrarlas rompería el día que alguien monte una hoja con esa zona, y lo
rompería en silencio.

Por eso se clasifican en dos:

  🟡 RUTA VIVA   el nombre aparece en el código que genera HTML (`motor/`,
                 `carta/`, `secciones/`). No se toca nunca.
  🔴 SIN RASTRO  el nombre no aparece en ningún sitio del código. Como no hay
                 forma de que se emita, borrar su regla **no puede** cambiar
                 lo que se imprime.

La poda es conservadora: solo elimina una regla si **TODOS** los selectores de
su lista están muertos. Una regla como `.hero-foto, .apuesta-foto { … }` se
queda entera, porque `.hero-foto` sí se usa.

Verificar después de podar
--------------------------
Borrar CSS no cambia el HTML, así que `verificar_split.py` no sirve de red
aquí. La prueba es visual:

    python3 render/hacer.py menu     # y comparar los PNG contra los de antes

Si un PNG cambia un solo byte, la poda se llevó algo vivo.

Uso
---
    python3 render/herramientas/css_sin_usar.py            # informe
    python3 render/herramientas/css_sin_usar.py --podar    # borra las 🔴
"""
import argparse
import re
import sys
from pathlib import Path

REND = Path(__file__).resolve().parent.parent

HTML_VIVOS = ["menu-completo.html", "tapas-final.html", "tapas.html",
              "habladores.html"]
HOJAS = ["estructura.css", "piel-parceros.css", "style.css", "hablador.css"]

# `hablador.css` se informa pero NO se poda: los habladores están en obra y
# tienen piezas sin activar (el de cumpleaños). Una clase «muerta» ahí puede
# ser sencillamente una pieza que todavía no se ha encendido.
NO_PODAR = {"hablador.css"}


def clases_usadas():
    usadas = set()
    for h in HTML_VIVOS:
        p = REND / h
        if not p.exists():
            continue
        for grupo in re.findall(r'class="([^"]+)"', p.read_text(encoding="utf-8")):
            usadas.update(grupo.split())
    return usadas


def codigo_que_genera_html():
    partes = []
    for patron in ("motor/*.py", "carta/*.py", "secciones/*.py", "*.py"):
        for p in REND.glob(patron):
            partes.append(p.read_text(encoding="utf-8"))
    return "\n".join(partes)


def reglas(css):
    """Trocea el CSS en (selector, cuerpo_completo). Entra en los @media."""
    fuera, i, n = [], 0, len(css)
    while i < n:
        llave = css.find("{", i)
        if llave == -1:
            fuera.append((None, css[i:]))
            break
        sel = css[i:llave].strip()
        prof, j = 1, llave + 1
        while j < n and prof:
            if css[j] == "{":
                prof += 1
            elif css[j] == "}":
                prof -= 1
            j += 1
        bloque = css[i:j]
        if sel.startswith("@") and "{" in css[llave + 1:j - 1]:
            fuera.append(("@anidado", bloque))       # @media: no se poda dentro
        else:
            fuera.append((sel, bloque))
        i = j
    return fuera


def selectores_de(sel):
    """Clases que aparecen en cada selector de la lista, una entrada por coma."""
    limpio = re.sub(r'/\*.*?\*/', '', sel, flags=re.S)
    return [set(re.findall(r'\.([a-zA-Z][a-zA-Z0-9_-]*)', s))
            for s in limpio.split(",") if s.strip()]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--podar", action="store_true",
                    help="borra las reglas cuyos selectores están TODOS muertos")
    args = ap.parse_args()

    usadas = clases_usadas()
    codigo = codigo_que_genera_html()

    total_podadas = 0
    for hoja in HOJAS:
        ruta = REND / hoja
        if not ruta.exists():
            continue
        css = ruta.read_text(encoding="utf-8")
        definidas = set(re.findall(r'\.([a-zA-Z][a-zA-Z0-9_-]*)',
                                   re.sub(r'/\*.*?\*/', '', css, flags=re.S)))
        sin_usar = definidas - usadas
        viva = {c for c in sin_usar
                if re.search(rf'''["'\s]{re.escape(c)}[\s"']''', codigo)}
        muerta = sin_usar - viva

        print(f"\n\033[1m{hoja}\033[0m — {len(definidas)} clases · "
              f"{len(definidas & usadas)} en uso")
        print(f"  🟡 ruta viva no ejercitada : {len(viva)}")
        print(f"  🔴 sin rastro en el código : {len(muerta)}")
        if muerta:
            print("     " + ", ".join(sorted(muerta)))

        if hoja in NO_PODAR:
            print("     (no se poda: pieza en obra)")
            continue
        if not args.podar or not muerta:
            continue

        salida, podadas = [], 0
        for sel, bloque in reglas(css):
            if sel and sel != "@anidado" and not sel.startswith("@"):
                grupos = selectores_de(sel)
                # Solo se poda si TODOS los selectores tocan clases y todas
                # esas clases están muertas. Un selector sin clase (`body`,
                # `:root`) hace que la regla se quede.
                if grupos and all(g and g <= muerta for g in grupos):
                    podadas += 1
                    continue
            salida.append(bloque)
        if podadas:
            ruta.write_text("".join(salida), encoding="utf-8")
            print(f"  ✂️  {podadas} reglas podadas · "
                  f"{len(css.splitlines())} → {len(''.join(salida).splitlines())} líneas")
            total_podadas += podadas

    if args.podar:
        print(f"\n✂️  {total_podadas} reglas podadas en total.")
        print("   ⚠️ Verifica AHORA que los PNG no cambiaron:")
        print("      python3 render/hacer.py menu")
    return 0


if __name__ == "__main__":
    sys.exit(main())
