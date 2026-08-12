#!/usr/bin/env python3
"""¿Sigue funcionando todo? Una respuesta, un comando.

Por qué existe
--------------
El proyecto tiene guardas excelentes y **repartidas**: `verificar_datos.py`
mira los datos, `auditar_resolucion.py` los dpi, `comparar_geometria.py` la
deriva HTML↔PDF, `partir_css.py --auditar` el reparto del CSS. Cada una
responde a su pregunta y ninguna responde a la única que importa después de
tocar algo gordo: **¿sigue saliendo lo mismo?**

Esa se venía contestando a mano, comparando hashes de PNG en una terminal. Y
lo que se comprueba a mano se deja de comprobar. El día que se dejó, se coló
una regresión real: al mudar el motor a un paquete, `estructura.css` cambió de
sitio y la auditoría del CSS quedó en «⛔ Falta estructura.css» — una guarda
que siempre falla es una guarda que nadie lee.

Qué comprueba, en orden de lo barato a lo caro
----------------------------------------------
1. **Las guardas de dato** — formato y tema concuerdan con el CSS, y cada
   declaración está del lado que dice el manifiesto.
2. **El menú se construye** y sus datos pasan (fotos que existen, ningún
   producto a dos precios, dpi suficientes).
3. **Las huellas** — cada PNG de pliego contra su hash de referencia. Esto es
   lo que de verdad contesta «¿salió lo mismo?».
4. **La deriva HTML↔PDF** (`--completo`), que cuesta ~2 min y solo hace falta
   al tocar maquetación.

El ritual de las huellas
------------------------
Igual que `verificar_split.py`: se fijan cuando lo que hay es correcto, y a
partir de ahí cualquier cambio de píxel se denuncia solo.

    menu-ia comprobar --fijar      # esto es lo bueno: guárdalo
    menu-ia comprobar              # ¿sigue siéndolo?

⚠️ **`--fijar` no valida nada.** Firma lo que haya en `output/`, sea correcto
o no. Se corre **después** de mirar los PNG, nunca antes — si se fija una
regresión, la regresión pasa a ser la referencia y la guarda protege el fallo.

Uso
---
    menu-ia comprobar
    menu-ia comprobar --completo    # incluye la deriva HTML↔PDF (~2 min)
    menu-ia comprobar --fijar
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys

from .proyecto import RAIZ, SALIDA

PY = sys.executable
HUELLAS = RAIZ / "huellas.json"


def _correr(etiqueta, modulo, args=()):
    r = subprocess.run([PY, "-m", modulo, *args], cwd=RAIZ.parent,
                       capture_output=True, text=True)
    ok = r.returncode == 0
    print(f"  {'✅' if ok else '⛔'} {etiqueta}")
    if not ok:
        cola = (r.stdout + r.stderr).strip().splitlines()
        for l in cola[-6:]:
            print(f"       {l}")
    return ok


def _pliegos():
    return sorted(SALIDA.glob("menu-doble-pagina-*.png"))


def _huella(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def fijar():
    pngs = _pliegos()
    if not pngs:
        print("⛔ No hay PNG en output/. Corre `menu-ia menu` primero.")
        return 1
    HUELLAS.write_text(json.dumps(
        {p.name: _huella(p) for p in pngs}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    print(f"✅ {len(pngs)} huellas fijadas en {HUELLAS.name}.\n"
          "   ⚠️ Esto firma lo que hay, no lo valida. Si acabas de fijar una\n"
          "      regresión, la guarda protegerá el fallo.")
    return 0


def comparar():
    if not HUELLAS.exists():
        print(f"  ⚠️ no hay {HUELLAS.name} — fija las huellas con --fijar")
        return None
    ref = json.loads(HUELLAS.read_text(encoding="utf-8"))
    actual = {p.name: _huella(p) for p in _pliegos()}
    faltan = sorted(set(ref) - set(actual))
    nuevos = sorted(set(actual) - set(ref))
    movidos = sorted(k for k in ref.keys() & actual.keys() if ref[k] != actual[k])
    if not (faltan or nuevos or movidos):
        print(f"  ✅ {len(ref)} pliegos idénticos a la referencia")
        return True
    for k in movidos:
        print(f"  🔴 CAMBIÓ  {k}")
    for k in faltan:
        print(f"  🔴 falta   {k}")
    for k in nuevos:
        print(f"  🟡 nuevo   {k}  (¿pliego añadido? fija las huellas)")
    return False


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fijar", action="store_true",
                    help="firma los PNG actuales como referencia")
    ap.add_argument("--completo", action="store_true",
                    help="añade la deriva HTML↔PDF (~2 min)")
    args = ap.parse_args()

    if args.fijar:
        return fijar()

    print(f"\n\033[1m▶ comprobar\033[0m — proyecto: {RAIZ}\n")
    ok = True

    print("Guardas de dato:")
    ok &= _correr("el formato concuerda con el CSS", "menu_ia.formato", ["--verificar"])
    ok &= _correr("el tema concuerda con el CSS", "menu_ia.tema", ["--verificar"])
    ok &= _correr("el reparto estructura/piel", "menu_ia.herramientas.partir_css",
                  ["--auditar"])

    print("\nConstrucción:")
    ok &= _correr("el menú se arma", "menu_ia.build_menu")
    ok &= _correr("los datos del menú", "menu_ia.herramientas.verificar_datos")
    ok &= _correr("resolución de las fotos", "menu_ia.auditar_resolucion")
    ok &= _correr("los PNG de pliego", "menu_ia.shot_spreads")

    print("\nHuellas:")
    h = comparar()
    ok &= (h is not False)

    if args.completo:
        print("\nDeriva HTML↔PDF (lento):")
        ok &= _correr("el PDF de trabajo", "menu_ia.build_pdf")
        ok &= _correr("nada se movió entre el HTML y el PDF",
                      "menu_ia.comparar_geometria")

    print()
    if ok and h:
        print("\033[1m✅ Todo en orden.\033[0m")
    elif ok:
        print("\033[1m🟡 Las guardas pasan, pero no hay referencia de huellas.\033[0m\n"
              "   Mira los PNG y, si son correctos: menu-ia comprobar --fijar")
    else:
        print("\033[1m⛔ Algo falla.\033[0m Arriba está qué.")
    if not args.completo:
        print("   (sin la deriva HTML↔PDF — añade --completo antes de imprimir)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
