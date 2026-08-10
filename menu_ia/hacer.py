#!/usr/bin/env python3
"""Entrada única para construir el menú. Un comando por entregable.

Por qué existe
--------------
`CLAUDE.md` documentaba ocho cadenas de comandos, el orden obligatorio entre
ellas y **una trampa**: si no corres `build_pdf.py` antes,
`comparar_geometria.py` lee el PDF viejo y denuncia como «desplazado» justo lo
que acabas de cambiar (§9.4). Esa trampa costó una sesión entera.

Un orden que hay que recordar es un error esperando su turno. Aquí está
escrito en código: cada receta lleva sus pasos, en su orden, y se para en el
primer fallo.

Uso
---
    python3 render/hacer.py                 # lista las recetas
    python3 render/hacer.py menu            # lo de todos los días
    python3 render/hacer.py verificar       # antes de dar por buena maquetación
    python3 render/hacer.py imprenta        # el archivo que se manda al taller
    python3 render/hacer.py menu --seco     # enseña los pasos sin correrlos
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

REND = Path(__file__).resolve().parent
RAIZ = REND.parent
PY = sys.executable


class Receta:
    def __init__(self, nombre, que, pasos, aviso=None, confirmar=False):
        self.nombre, self.que, self.pasos = nombre, que, pasos
        self.aviso, self.confirmar = aviso, confirmar


RECETAS = [
    Receta(
        "menu", "El menú y sus PNG de pliego — lo de todos los días",
        # Las dos comprobaciones van DESPUÉS de generar y ANTES de los PNG:
        # exportar 7 imágenes de un menú con una foto rota es tiempo tirado, y
        # el hueco no se ve hasta que alguien compara el peso de los archivos.
        # Juntas tardan ~3 s sobre un build de ~8 s: barato para lo que evitan.
        # `formato.py --verificar` va PRIMERO y cuesta milisegundos: si
        # `style.css` no concuerda con el formato activo, Chromium maqueta con
        # una caja y el PDF declara otra. No da error en ningún paso — da un
        # TrimBox que no cuadra con lo dibujado, y eso se ve en la plancha.
        [("formato.py", ["--verificar"]),
         ("tema.py", ["--verificar"]),
         ("build_menu.py", []),
         ("herramientas/verificar_datos.py", []),
         ("auditar_resolucion.py", []),
         ("shot_spreads.py", []),
         ("build_precios.py", [])],
    ),
    Receta(
        "menu-en", "El menú EN INGLÉS y sus PNG — mismo diseño, mismos precios",
        # La guarda de traducción va DESPUÉS de generar y ANTES de los PNG,
        # exactamente por el mismo motivo que `verificar_datos.py` en la receta
        # `menu`: exportar 7 imágenes con una frase en español metida en medio
        # es tiempo tirado, y ese fallo NO se ve en el HTML — se ve en el PNG,
        # si alguien mira esa esquina.
        # `build_precios.py` NO entra: los precios son los mismos y PRECIOS.md
        # es un documento en español para el dueño, no un entregable del menú.
        [("build_menu.py", ["--idioma", "en"]),
         ("build_tapas_final.py", ["--idioma", "en"]),
         ("herramientas/verificar_traduccion.py", ["--idioma", "en"]),
         ("herramientas/verificar_datos.py", []),
         ("shot_spreads.py", ["--idioma", "en"])],
        aviso="El inglés NO tiene precios ni fotos propias: los lee de "
              "`secciones/` igual que el español. Aquí solo viaja el texto "
              "(`idiomas/en.py`). Si un precio está mal, se arregla en su "
              "sección y se arregla en los dos idiomas a la vez.",
    ),
    Receta(
        "plano-en", "Las 16 páginas en inglés, aplanadas",
        [("build_tapas_final.py", ["--idioma", "en"]),
         ("build_pdf_plano.py", ["--idioma", "en"])],
    ),
    Receta(
        "tapas", "Portada y contraportada, por su propio camino",
        [("build_tapas.py", []),
         ("shot_tapas.py", [])],
    ),
    Receta(
        "pdf", "PDF de trabajo — el menú entero en una pieza",
        [("build_pdf.py", [])],
        aviso="Sale en RGB y con transparencia viva. Para trabajar, NO para "
              "enseñar ni entregar: hay lectores que resuelven mal la "
              "transparencia y sacan bloques grises donde debería haber "
              "difuminado. Lo que sale del proyecto va aplanado (`plano`).",
    ),
    Receta(
        "plano", "Las 16 páginas aplanadas, con el texto todavía en vector",
        [("build_tapas_final.py", []),
         ("build_pdf_plano.py", [])],
    ),
    Receta(
        "web", "El PDF para descargar de internet — ligero, en sRGB",
        # `build_menu.py` va delante aunque el HTML español suela estar recién
        # hecho: esta receta se corre de tarde en tarde y toma el HTML que haya
        # en disco. El 2026-08-07 ese HTML venía pisado por la guarda de
        # traducción y la página 3 salió en inglés (§9.6). La causa está
        # arreglada; reconstruir cuesta medio segundo y quita la dependencia de
        # qué se corrió antes.
        [("build_menu.py", []),
         ("build_tapas_final.py", []),
         ("build_pdf_plano.py", ["--web"])],
        aviso="Sale output/web/menu-parceros-web.pdf: mismo aplanado que el de "
              "imprenta —texto en vector, fotos rasterizadas— pero a 144 dpi, "
              "sin sangrado y en sRGB. Pesa ~17 veces menos que el aplanado de "
              "revisión, que es lo que decide si alguien lo abre desde el "
              "celular.\n"
              "   NO sirve para el taller: va en RGB y sin control de tintas.",
    ),
    Receta(
        "web-en", "El PDF para internet, EN INGLÉS",
        # Las mismas dos guardas que `imprenta-en`, y por el mismo motivo: una
        # frase en español dentro del PDF inglés no se ve en el HTML.
        [("build_menu.py", ["--idioma", "en"]),
         ("build_tapas_final.py", ["--idioma", "en"]),
         ("herramientas/verificar_traduccion.py", ["--idioma", "en"]),
         ("herramientas/medir_desborde.py", ["--idioma", "en"]),
         ("build_pdf_plano.py", ["--web", "--idioma", "en"])],
    ),
    Receta(
        "verificar", "¿Se movió algo entre el HTML y el PDF? (§9.4)",
        # `build_pdf.py` va PRIMERO y no es opcional: `comparar_geometria.py`
        # lee output/menu-completo.pdf y NO lo reconstruye. Con el PDF viejo,
        # lo que acabas de cambiar se denuncia a sí mismo como desplazado.
        # Esta es la razón de ser de todo este archivo.
        [("build_pdf.py", []),
         ("auditar_resolucion.py", ["--pdf"]),
         ("comparar_geometria.py", [])],
    ),
    Receta(
        "imponer", "Versión impuesta para grapa — solo si la imprenta la pide",
        [("imponer_pdf.py", [])],
        aviso="Casi todas las imprentas prefieren orden de lectura e imponen "
              "ellas. Esto es la alternativa, no el entregable.",
    ),
    Receta(
        "imprenta", "EL ARCHIVO QUE SE MANDA AL TALLER",
        [("build_pdf_plano.py", ["--imprenta"]),
         ("preparar_pdf_imprenta.py", [])],
        aviso="Sale output/imprenta/menu-parceros-CMYK-sangrado.pdf: 16 "
              "páginas, todo en CMYK, sangrado y TrimBox declarados. El "
              "`--imprenta` apaga los marcadores `.pendiente` — anotaciones de "
              "producción que no viajan a la plancha.\n"
              "   El perfil sigue siendo el Generic CMYK de macOS; §1 pide "
              "FOGRA39. Hay que preguntarle al taller.",
        confirmar=True,
    ),
    Receta(
        "imprenta-en", "EL ARCHIVO DEL TALLER, EN INGLÉS",
        # Las dos guardas van ANTES de aplanar, no después. Aplanar a 400 dpi
        # son ~40 s y separar a CMYK otro tanto: descubrir en el PDF final que
        # una frase salió en español significa repetir los dos pasos. Y si no
        # se descubre, se descubre en la plancha.
        [("build_menu.py", ["--idioma", "en"]),
         ("build_tapas_final.py", ["--idioma", "en"]),
         ("herramientas/verificar_traduccion.py", ["--idioma", "en"]),
         ("herramientas/medir_desborde.py", ["--idioma", "en"]),
         ("build_pdf_plano.py", ["--imprenta", "--idioma", "en"]),
         ("preparar_pdf_imprenta.py", ["--idioma", "en"])],
        aviso="Sale output/imprenta/menu-parceros-CMYK-sangrado-en.pdf, "
              "hermano del español y con el MISMO perfil, límite de tinta y "
              "cajas: los dos se tiran en la misma máquina sin recalibrar.\n"
              "   El sufijo `-en` del nombre no es cosmético — los dos archivos "
              "van al mismo taller y solo se distinguen por el texto de dentro.\n"
              "   Sigue pendiente FOGRA39 para LOS DOS: se exporta con el "
              "Generic CMYK de macOS. Hay que preguntarle al taller.",
        confirmar=True,
    ),
    Receta(
        "habladores", "Las piezas de mesa (150 × 210 mm)",
        [("build_habladores.py", []),
         ("shot_habladores.py", []),
         ("build_pdf_habladores.py", [])],
    ),
    Receta(
        "split", "¿El reparto de render/ sigue sano? (lo que lee build_menu.py "
                 "por ruta sigue corriendo)",
        [("herramientas/verificar_split.py", [])],
        aviso="Esto NO compara el HTML contra un hash fijo: el contenido cambia "
              "a diario y estaría rojo siempre. La comparación byte a byte es el "
              "ritual de un re-split: `--fijar` antes, `--contra-referencia` "
              "después.",
    ),
]

POR_NOMBRE = {r.nombre: r for r in RECETAS}


def listar():
    print("Recetas disponibles:\n")
    for r in RECETAS:
        marca = " ⚠️" if r.confirmar else ""
        print(f"  \033[1m{r.nombre:<12}\033[0m {r.que}{marca}")
        for script, args in r.pasos:
            print(f"               · {script} {' '.join(args)}".rstrip())
        print()
    print("  python3 render/hacer.py <receta> [--seco]")


def correr(receta, seco=False):
    print(f"\n\033[1m▶ {receta.nombre}\033[0m — {receta.que}")
    if receta.aviso:
        print(f"\n⚠️  {receta.aviso}\n")

    if receta.confirmar and not seco:
        # CLAUDE.md: el archivo de imprenta se genera «solo cuando el dueño lo
        # confirme». Durante la iteración se trabaja sobre el HTML y los PNG.
        r = input("¿Generar el archivo de imprenta? [escribe «sí»] ").strip().lower()
        if r not in ("sí", "si", "s"):
            print("Cancelado.")
            return 1

    for i, (script, args) in enumerate(receta.pasos, 1):
        etiqueta = f"{script} {' '.join(args)}".strip()
        print(f"  [{i}/{len(receta.pasos)}] {etiqueta}")
        if seco:
            continue
        t0 = time.monotonic()
        r = subprocess.run([PY, str(REND / script), *args], cwd=RAIZ)
        if r.returncode != 0:
            print(f"\n⛔ Falló `{etiqueta}` (código {r.returncode}).")
            print("   Los pasos siguientes NO se corren: dependen de este.")
            return r.returncode
        print(f"      ✓ {time.monotonic() - t0:.1f}s")

    print(f"\n✅ {receta.nombre} completo." if not seco else "\n(--seco)")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("receta", nargs="?", help="qué construir")
    ap.add_argument("--seco", action="store_true",
                    help="enseña los pasos sin correrlos")
    args = ap.parse_args()

    if not args.receta:
        listar()
        return 0
    if args.receta not in POR_NOMBRE:
        print(f"⛔ No conozco la receta «{args.receta}».\n")
        listar()
        return 2
    return correr(POR_NOMBRE[args.receta], args.seco)


if __name__ == "__main__":
    sys.exit(main())
