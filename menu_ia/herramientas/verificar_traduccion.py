#!/usr/bin/env python3
"""Guarda del menú en inglés. Se planta si el catálogo miente.

Es la hermana de `verificar_datos.py`, y existe por el mismo motivo: un menú
impreso es una promesa que dura todo el tiraje, y los tres fallos que vigila
**no se ven en el HTML** — se ven en el PNG, si alguien mira esa esquina.

🔴 PARA EL BUILD
   1. **Texto sin traducir.** Se imprimiría la frase en español en medio de la
      página inglesa. Pasa solo con cambiar una coma en `secciones/`: la clave
      del catálogo deja de existir y `t()` devuelve el original.
   2. **Gancho perdido.** Si el español parte gancho y cuerpo con `\\n` y la
      traducción no, esa ficha se imprime como párrafo corrido sin
      seminegrilla (§6.17.7e) — y son ~30 fichas.
   3. **Token `[[hoja:…]]` perdido.** Es la ramita SVG pegada a «guascas»
      (§6.30-quater). Sin el token, el texto imprime los corchetes literales.
   4. **Esqueleto distinto.** Si el HTML en inglés no tiene exactamente las
      mismas cajas que el español, una traducción rompió el marcado.

🟡 AVISA
   · Entradas del catálogo que ya no imprime nadie (texto en español cambiado
     o platillo dado de baja). No para el build —no se imprime nada malo— pero
     es catálogo muerto que confunde en la siguiente ronda.

Uso
---
    python3 render/herramientas/verificar_traduccion.py           # inglés
    python3 render/herramientas/verificar_traduccion.py --idioma en
"""
import argparse
import collections
import contextlib
import importlib.util
import io
import re
import sys
from pathlib import Path

# La raíz es la del CLIENTE, no la del paquete: aquí están su HTML, su
# CSS y sus datos. Deducirla de `__file__` daba site-packages.
from ..proyecto import RAIZ as REND
sys.path.insert(0, str(REND))

from ..motor import idioma  # noqa: E402

# Cajas cuyo número tiene que coincidir entre los dos idiomas. Son las que
# sostienen el reparto de la página: si cambia una, cambió la maqueta.
CAJAS = ("desc", "desc-gancho", "nombre-display", "hero-lista", "adic-linea",
         "fila", "card", "texto-item", "mini-titulo", "cruce-linea")

# Todo lo que escriben los dos scripts que esta guarda ejecuta. Se restaura al
# terminar — ver `_artefactos_intactos`.
ARTEFACTOS = ("menu-completo.html", "menu-completo-en.html",
              "spreads-activos.json", "spreads-activos-en.json",
              "tapas-final.html", "tapas-final-en.html")


@contextlib.contextmanager
def _artefactos_intactos():
    """Deja el disco como estaba: esta guarda **comprueba**, no construye.

    ⚠️ Por qué hace falta (2026-08-07). `build_menu.py` hace su trabajo **al
    importarse**, y aquí se importa dos veces: una en inglés y otra en español,
    para comparar los dos esqueletos. La segunda pasada reescribe
    `menu-completo.html` —el del español, el bueno— y lo hace con los módulos
    de `secciones/` ya cacheados en inglés por la primera: sale un HTML
    **mezclado**, español casi todo y con la hoja de Bebidas en inglés.

    No se ve. El build termina en verde, el HTML pesa lo mismo, y quien corra
    después `hacer.py plano`, `web` o **`imprenta`** —ninguna reconstruye el
    HTML español— se lleva esa página al PDF. Ya pasó: el primer
    `menu-parceros-web.pdf` salió con la página 3 en inglés.

    La guarda no puede dejar de escribir sin partir `build_menu.py` en módulo y
    script; restaurar lo que había es la red barata y no depende de que nadie
    recuerde el orden.
    """
    previo = {n: (REND / n).read_bytes() for n in ARTEFACTOS
              if (REND / n).exists()}
    try:
        yield
    finally:
        for nombre, datos in previo.items():
            destino = REND / nombre
            if destino.read_bytes() != datos:
                destino.write_bytes(datos)
        # Lo que no existía antes tampoco existe después.
        for nombre in ARTEFACTOS:
            if nombre not in previo and (REND / nombre).exists():
                (REND / nombre).unlink()


def _construir(script, codigo, etiqueta):
    """Corre un script de build en un idioma y devuelve su HTML."""
    idioma.fijar(codigo)
    spec = importlib.util.spec_from_file_location(f"_{etiqueta}_{codigo}",
                                                  REND / script)
    mod = importlib.util.module_from_spec(spec)
    argv, cwd = sys.argv, Path.cwd()
    sys.argv = [script, "--idioma", codigo]
    try:
        # ⚠️ `build_tapas_final.py` resuelve `assets/` como ruta RELATIVA al
        # directorio de trabajo, no a `REND`. Sin este `chdir`, la guarda solo
        # pasa si se lanza desde la raíz del repo — y falla con un
        # FileNotFoundError de una fuente que no menciona ni al idioma ni a
        # las tapas.
        import os
        os.chdir(REND.parent)
        with contextlib.redirect_stdout(io.StringIO()):
            spec.loader.exec_module(mod)
    finally:
        sys.argv = argv
        os.chdir(cwd)
    return mod.SALIDA.read_text(encoding="utf-8")


def _render(codigo):
    """Construye el menú ENTERO —interior y las dos tapas— en un idioma.

    Las tapas entran a propósito: llevan el claim de cierre, el panel de
    cumpleaños y el horario, y son las dos páginas que más mira quien recibe
    la carta. Sin ellas, la guarda daba por muerto medio catálogo.
    """
    idioma.CAPTURA = []
    interior = _construir("build_menu.py", codigo, "bm")
    tapas = _construir("build_tapas_final.py", codigo, "tf")
    pedidos, idioma.CAPTURA = idioma.CAPTURA, None
    return interior, tapas, pedidos


def _comprobar():
    ap = argparse.ArgumentParser()
    ap.add_argument("--idioma", default="en")
    args = ap.parse_args()
    cod = args.idioma

    errores, avisos = [], []

    # ── 1 · Textos sin traducir ──────────────────────────────────────────
    idioma.fijar(cod)
    catalogo = dict(idioma._CATALOGO)
    html_en, tapas_en, pedidos = _render(cod)
    for texto, veces in sorted(idioma.FALTAN.items()):
        errores.append(f"sin traducir ({veces}×): {texto[:90]}")
    # Se copia AHORA: el render en español de más abajo llama a `fijar("es")`,
    # que vacía este registro.
    nombres_es = sorted(k for k, v in idioma.NOMBRES_VISTOS.items() if v is None)

    # ── 2-3 · Gancho y tokens que tienen que sobrevivir ──────────────────
    impresos = {idioma._norm(s) for s in pedidos}
    for es, en in catalogo.items():
        if es not in impresos:
            continue
        if "\n" in es and "\n" not in en:
            errores.append(
                f"la traducción perdió el corte de gancho: {en[:70]}")
        for token in re.findall(r"\[\[hoja:[^\]]+\]\]", es):
            if token not in en:
                errores.append(
                    f"la traducción perdió {token}: {en[:70]}")

    # ── 4 · Mismo esqueleto que el español ───────────────────────────────
    html_es, tapas_es, _ = _render("es")
    idioma.fijar("es")
    for caja in CAJAS:
        pat = re.compile(rf'class="[^"]*\b{re.escape(caja)}\b')
        a, b = len(pat.findall(html_es)), len(pat.findall(html_en))
        if a != b:
            errores.append(f"«{caja}»: {a} cajas en español y {b} en {cod}")
    # Las tapas llevan HTML DENTRO de los propios textos (`<br>`, `<b>`): si
    # una traducción se come una etiqueta, el renglón se parte donde no debe.
    for etiqueta in ("br", "b"):
        pat = re.compile(rf"<{etiqueta}>")
        a, b = len(pat.findall(tapas_es)), len(pat.findall(tapas_en))
        if a != b:
            errores.append(
                f"tapas: {a} «<{etiqueta}>» en español y {b} en {cod} — "
                f"una traducción perdió una etiqueta")

    # ── 🟡 Catálogo muerto ───────────────────────────────────────────────
    for es in catalogo:
        if es not in impresos:
            avisos.append(f"ya no se imprime: {es[:80]}")

    for a in avisos:
        print(f"🟡 {a}")
    for e in errores:
        print(f"🔴 {e}")

    # ── Nombres que se quedan en español ─────────────────────────────────
    # No es un error —es la regla— pero se listan porque son la única parte
    # del menú que la guarda NO puede juzgar sola: si mañana entra una bebida
    # que se llama «Jarra de sabor del día», ese nombre saldrá en español y
    # nada se pondrá rojo. Verlos juntos al cerrar es lo que hace que se note.
    quedan = nombres_es
    if quedan:
        print(f"\nℹ️  {len(quedan)} nombres se imprimen en español (regla del "
              f"dueño). Revisa que ninguno sea en realidad una descripción:")
        for k in quedan:
            print(f"     · {k}")

    n = len(impresos)
    if errores:
        print(f"\n⛔ {len(errores)} problema(s) en el menú en «{cod}».")
        raise SystemExit(1)
    print(f"\n✅ {n} textos impresos, todos traducidos · esqueleto idéntico "
          f"al español · ganchos y tokens intactos")


def main():
    # El `with` envuelve TODO, incluido el `SystemExit(1)` de la comprobación:
    # una guarda que se planta tiene que dejar el disco tan intacto como una
    # que pasa, o el arreglo del error se haría sobre un HTML pisado.
    with _artefactos_intactos():
        _comprobar()


if __name__ == "__main__":
    main()
