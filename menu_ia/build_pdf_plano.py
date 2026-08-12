#!/usr/bin/env python3
"""PDF aplanado: fondo rasterizado + texto vectorial encima. Sin transparencia viva.

**Por qué existe.** `build_pdf.py` saca un PDF correcto pero con **100 máscaras
suaves de luminosidad** (`/SMask /S /Luminosity`): así escribe Chromium todo lo
difuminado —sombras de caja, sombras de texto, los degradados del scrim—. Es
transparencia *viva*, y dos cosas la vuelven un riesgo real en un impreso:

  1. **No todos los lectores la resuelven igual.** El visor del proyecto pinta
     el rectángulo entero opaco en vez del difuminado: bloques grises tras las
     fotos del Menú Infantil y bloques negros tras el texto del hero de
     Entradas. El archivo es válido; el resultado, no.
  2. **PDF/X-1a la prohíbe.** Es el perfil que pide casi cualquier imprenta, y
     obliga a entregar la transparencia ya resuelta.

**Qué hace.** Lo mismo que un aplanador profesional, en dos pasadas del MISMO
motor que genera los PNG de revisión:

  · **Fondo** — la página entera menos el relleno de las letras, rasterizada a
    400 dpi. Ahí quedan resueltas las fotos, los degradados y todas las
    sombras, incluidas las del texto (que se dibujan a partir de la silueta de
    la letra y **sobreviven** a `-webkit-text-fill-color: transparent`, que es
    justo la propiedad que apaga el relleno **sin tocar los SVG**, que pintan
    con `fill: currentColor`).
  · **Texto** — solo el relleno de las letras, en vector, sobre fondo
    transparente. Sigue siendo texto: nítido a cualquier tamaño y, al separar a
    CMYK, negro de una sola tinta. Rasterizarlo también habría sido más simple,
    pero un negro de texto construido con cuatro tintas enseña el desregistro
    de la máquina en cuerpos de 7 pt, que es casi todo este menú.

Las dos pasadas comparten maqueta —solo se apaga pintura, nunca se cambia una
caja—, así que no pueden descuadrarse. Se verifica igual: `comparar_geometria.py`.

    python3 render/build_pdf_plano.py              # las 16 páginas, tapas incluidas
    python3 render/build_pdf_plano.py --sin-tapas  # solo el interior
"""
from __future__ import annotations

import argparse
import asyncio
import io
import json
from pathlib import Path

import fitz
from PIL import Image
from playwright.async_api import async_playwright

from . import variantes as idiomas
from .formato import PAGINA_MM, SANGRADO_MM
from .formato import ACTIVO as _FMT

PAGINAS_TAPAS = _FMT.paginas_tapas

# 🏷️ Quién produce el archivo y cómo se llama. Estaba escrito «Parceros
# Café» en los METADATOS del PDF: el archivo de imprenta de cualquier otro
# cliente habría declarado que lo produjo Parceros. No se ve en la página —
# se ve al abrir Propiedades del documento, y ahí ya está en el taller.
# 🏷️ Cómo se llama el cliente en los nombres de archivo.
#
# ⚠️ Salía del nombre del MÓDULO de contenido, con Parceros escrito como caso
# especial: `'parceros' if MENU_CARTA == 'secciones'`. Dos problemas. Uno, el
# motor conocía a un cliente por su nombre. Dos, cualquier proyecto creado con
# `menu-ia crear` tiene su carta en un paquete llamado `carta`, así que su
# archivo de imprenta salía como **`menu-carta-CMYK-sangrado.pdf`** — nombrado
# por el módulo, no por el restaurante. Eso es lo que llega al taller.
#
# Ahora lo dice la marca: `SLUG` de la carta, o el tema activo.
import os  # noqa: E402


def _cliente():
    import importlib
    try:
        c = importlib.import_module(os.environ.get("MENU_CARTA", "secciones"))
        s = getattr(c, "SLUG", None)
        if s:
            return str(s)
    except ModuleNotFoundError:
        pass
    from . import tema as _t
    return (_t.ACTIVO.nombre or "menu").replace("_", "-")


CLIENTE = _cliente()

# La raíz es la del CLIENTE, no la del paquete: aquí están su HTML, su
# CSS y sus datos. Deducirla de `__file__` daba site-packages.
from .proyecto import RAIZ as REND
SRC = REND / "menu-completo.html"
from .proyecto import SALIDA as OUT

DPI = 400
PX_MM = 96 / 25.4
# `PAGINA_MM` y `SANGRADO_MM` llegan de `formato.py` (fuente única). Estaban
# tecleados aquí y en otros cuatro sitios; ver la cabecera de ese módulo.

# El menú para pantalla. Mismo aplanado que el de imprenta —fondo rasterizado y
# texto en vector—, con tres cosas cambiadas y una razón para cada una:
#
#   · **144 dpi** en vez de 400. Es 1.5× la densidad de un CSS pixel: cubre el
#     zoom normal de un visor y se defiende en pantalla Retina, y pesa **ocho
#     veces menos** que 400 (el peso va con el cuadrado de los dpi).
#   · **JPEG q72 con submuestreo 4:2:0.** En el aplanado el texto NO viaja en
#     el JPEG, así que lo único que sufre el submuestreo son los bordes de
#     color de las fotos, que a este tamaño nadie ve. Es lo que hace barata la
#     pieza sin tocar la nitidez de la carta.
#   · **Sin sangrado y en sRGB.** Nadie va a guillotinar esto, y el navegador
#     no gestiona color: el CMYK de imprenta se vería apagado en pantalla.
WEB = {"dpi": 144, "calidad": 72, "submuestreo": 2}

# El menú son 16 páginas: portada, 14 de contenido y contraportada. Las tapas
# viven en su propio HTML pero comparten geometría (192 × 285 mm con sangrado),
# así que entran en el mismo documento sin adaptar nada.
#
# `tapas-final.html` trae las dos tapas DOS veces —en orden de lectura y en
# orden de imprenta— más sus rótulos de revisión. Por eso cada tapa se saca con
# un CSS que esconde todo lo demás: así la pasada imprime exactamente una
# página y no hay que adivinar qué índice le tocó.
OCULTA_TAPAS = "#orden-imprenta, .rotulo { display: none !important; }"

def fuentes(idioma="es"):
    """Las tres pasadas del documento, con los HTML del idioma pedido.

    Es función y no constante desde que existe la versión en inglés: los tres
    nombres de archivo cambian a la vez (`-en`), y una constante obligaría a
    reasignarla desde `main()` — que es justo el patrón con el que se cuela un
    PDF mezclando la portada de un idioma con el interior del otro.
    """
    suf = idiomas.sufijo(idioma)
    tapas, interior = f"tapas-final{suf}.html", f"menu-completo{suf}.html"
    interior_solo = [{"html": interior, "etiqueta": "interior", "solo": ""}]
    # 📌 Un formato puede no tener tapas. `paginas_tapas` es 2 en el cuadernillo
    # —portada y contraportada, que viven en su propio HTML— y 0 en una hoja
    # suelta. Antes las tres pasadas eran fijas, así que montar una hoja suelta
    # petaba buscando un `tapas-final.html` que ese cliente nunca tendrá.
    if not PAGINAS_TAPAS:
        return interior_solo
    return [
        {"html": tapas, "etiqueta": "portada",
         "solo": OCULTA_TAPAS + "#orden-lectura .page.contra { display: none !important; }"},
        *interior_solo,
        {"html": tapas, "etiqueta": "contraportada",
         "solo": OCULTA_TAPAS + "#orden-lectura .page.portada { display: none !important; }"},
    ]

# Apaga el RELLENO de las letras y nada más. `-webkit-text-fill-color` actúa
# solo sobre texto: los iconos SVG (que heredan `fill: currentColor`) siguen
# pintando, y las sombras de texto también, porque salen de la silueta.
CSS_FONDO = """
  *, *::before, *::after { -webkit-text-fill-color: transparent !important; }
"""

# Deja SOLO el relleno de las letras. `visibility: hidden` en las imágenes
# conserva la caja, así que la maqueta no se mueve ni un micrón.
CSS_TEXTO = """
  img, svg, video { visibility: hidden !important; }
  *, *::before, *::after {
    background: none !important;
    box-shadow: none !important;
    text-shadow: none !important;
    filter: none !important;
    border-color: transparent !important;
    outline-color: transparent !important;
  }
"""


# §1.3 del style-guide: los marcadores de producción no viajan a la plancha. Es
# una anotación para el equipo —«esto todavía no está cerrado»— y en el papel se
# leería como parte del diseño. Se apaga aquí, no se borra del HTML: mientras el
# asunto siga abierto tiene que seguir viéndose en los PNG de revisión.
CSS_IMPRENTA = ".pendiente { display: none !important; }"


def _titulo_web():
    """El título que ve el navegador al abrir el PDF. Lo pone la carta."""
    import importlib
    c = importlib.import_module(os.environ.get("MENU_CARTA", "secciones"))
    return getattr(c, "TITULO", {}).get("es", CLIENTE)


async def capturar_fuente(pg, fuente, dpi, extra=""):
    """Rasteriza los fondos y saca el PDF de texto de UNA fuente HTML."""
    ruta = REND / fuente["html"]
    await pg.goto(ruta.as_uri())
    await pg.wait_for_function(
        "() => [...document.images].every(i => i.complete && i.naturalWidth > 0)",
        timeout=180000)
    await pg.evaluate("document.fonts.ready")
    await pg.emulate_media(media="print")
    if fuente["solo"]:
        await pg.add_style_tag(content=fuente["solo"])
    if extra:
        await pg.add_style_tag(content=extra)
    await pg.wait_for_timeout(1200)

    await pg.add_style_tag(content=CSS_FONDO)
    await pg.wait_for_timeout(600)
    secciones = [s for s in await pg.query_selector_all("section.page")
                 if await s.is_visible()]
    fondos = []
    for i, s in enumerate(secciones):
        fondos.append(await s.screenshot(type="png"))
        print(f"  · {fuente['etiqueta']}: fondo {i + 1}/{len(secciones)} a {dpi} dpi")

    await pg.add_style_tag(content=CSS_TEXTO + """
      *, *::before, *::after { -webkit-text-fill-color: initial !important; }
    """)
    await pg.wait_for_timeout(600)
    # ⚠️ `print_background=True` es obligatorio aunque aquí no haya ningún
    # fondo que pintar —los quita `CSS_TEXTO`—. Con el flag apagado,
    # Chromium **oscurece el texto claro** para que no se pierda sobre papel
    # blanco: el crema del título salía a #a29a95, un 35 % más oscuro, y el
    # amarillo a #977f34. El DOM seguía diciendo el color bueno; quien lo
    # cambiaba era el escritor de PDF.
    texto_pdf = await pg.pdf(print_background=True, prefer_css_page_size=True)
    return fondos, texto_pdf


async def capturar(dpi: int, fuentes, extra=""):
    escala = dpi / 96
    piezas = []
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1000, "height": 1400},
                              device_scale_factor=escala)
        for fuente in fuentes:
            fondos, texto_pdf = await capturar_fuente(pg, fuente, dpi, extra)
            piezas.append((fuente["etiqueta"], fondos, texto_pdf))
        await b.close()
    return piezas


def componer(piezas, salida: Path, calidad=95, submuestreo=0,
             recortar=False, titulo=None):
    doc = fitz.open()
    w_pt, h_pt = PAGINA_MM[0] / 25.4 * 72, PAGINA_MM[1] / 25.4 * 72
    caja = fitz.Rect(0, 0, w_pt, h_pt)
    # El sangrado existe para la guillotina. En pantalla nadie lo corta, así
    # que la versión web enseña la página ya refilada: se declara `CropBox`,
    # no se recorta el fondo — la maqueta sigue cuadrando con la de imprenta y
    # `comparar_geometria.py` puede seguir midiendo las dos contra el mismo HTML.
    refile = SANGRADO_MM / 25.4 * 72
    corte = fitz.Rect(refile, refile, w_pt - refile, h_pt - refile)
    for _, fondos, texto_pdf in piezas:
        src = fitz.open(stream=texto_pdf, filetype="pdf")
        if src.page_count != len(fondos):
            raise SystemExit(
                f"descuadre: {len(fondos)} fondos y {src.page_count} páginas de "
                f"texto. El CSS de recorte no dejó una página por sección.")
        for i, fondo in enumerate(fondos):
            pagina = doc.new_page(width=w_pt, height=h_pt)
            # JPEG 4:4:4 de calidad alta: el fondo son fotos y planos de color,
            # y no lleva dentro tipografía que pueda sufrir con la compresión.
            # En web baja la calidad y entra el submuestreo de color (4:2:0):
            # el peso manda, y el texto —que es lo que sufriría— no está aquí.
            im = Image.open(io.BytesIO(fondo)).convert("RGB")
            buf = io.BytesIO()
            im.save(buf, "JPEG", quality=calidad, subsampling=submuestreo,
                    optimize=True)
            pagina.insert_image(caja, stream=buf.getvalue())
            # El texto entra como Form XObject: sigue siendo vectorial.
            pagina.show_pdf_page(caja, src, i)
            if recortar:
                pagina.set_cropbox(corte)
        src.close()
    if titulo:
        from . import tema as _t
        doc.set_metadata({"title": titulo,
                          "producer": _t.ACTIVO.lema or _t.ACTIVO.nombre})
    # Sin «fast web view»: MuPDF quitó la linearización («Linearisation is no
    # longer supported») y aquí no hay qpdf. Importa poco a este tamaño —el
    # archivo entero pesa menos que una foto del menú—, pero si algún día se
    # sirve desde una web lenta, `qpdf --linearize` lo arregla en un paso.
    doc.save(salida, deflate=True, garbage=4)
    doc.close()


def contar_transparencia(ruta: Path) -> int:
    doc = fitz.open(ruta)
    n = sum(1 for x in range(1, doc.xref_length())
            if "/Luminosity" in (doc.xref_object(x) or ""))
    doc.close()
    return n


def main():
    ap = argparse.ArgumentParser()
    # Sin valor por omisión: lo pone `--web` o lo pone `DPI`. Con `default=DPI`
    # no hay forma de distinguir «no lo pidió» de «pidió 400», y `--web --dpi 400`
    # exportaría a 144 en silencio.
    ap.add_argument("--dpi", type=int, default=None)
    ap.add_argument("--sin-tapas", action="store_true",
                    help="solo las 14 páginas de contenido")
    ap.add_argument("--salida", default=None)
    ap.add_argument("--imprenta", action="store_true",
                    help="apaga los marcadores .pendiente (§1.3): lo que sale "
                         "del proyecto no lleva anotaciones de producción")
    ap.add_argument("--web", action="store_true",
                    help="versión ligera para descargar desde internet: fondo "
                         f"a {WEB['dpi']} dpi, sin sangrado y sin marcadores")
    ap.add_argument("--calidad", type=int, default=None,
                    help="calidad JPEG del fondo (95 por omisión, "
                         f"{WEB['calidad']} en --web)")
    ap.add_argument("--idioma", default="es", choices=idiomas.DISPONIBLES,
                    help="idioma del documento (es por omisión)")
    args = ap.parse_args()

    # `--web` sale del proyecto igual que el de imprenta, así que se lleva su
    # misma regla: los marcadores `.pendiente` son notas para el equipo (§1.3).
    dpi = args.dpi or (WEB["dpi"] if args.web else DPI)
    calidad = args.calidad or (WEB["calidad"] if args.web else 95)
    limpio = args.imprenta or args.web

    todas = fuentes(args.idioma)
    piezas_fuente = ([f for f in todas if f["etiqueta"] == "interior"]
                     if args.sin_tapas else todas)
    suf = idiomas.sufijo(args.idioma)
    nombre = (f"menu-interior-plano{suf}.pdf" if args.sin_tapas
              else f"menu-{CLIENTE}-web{suf}.pdf" if args.web
              else f"menu-completo-plano-imprenta{suf}.pdf" if args.imprenta
              else f"menu-completo-plano{suf}.pdf")
    if args.salida:
        salida = Path(args.salida).resolve()
    elif args.web:
        (OUT / "web").mkdir(parents=True, exist_ok=True)
        salida = OUT / "web" / nombre
    else:
        salida = OUT / nombre

    piezas = asyncio.run(capturar(dpi, piezas_fuente,
                                  CSS_IMPRENTA if limpio else ""))
    componer(piezas, salida, calidad=calidad,
             submuestreo=WEB["submuestreo"] if args.web else 0,
             recortar=args.web,
             titulo=_titulo_web() if args.web else None)

    n = contar_transparencia(salida)
    doc = fitz.open(salida)
    total, mb = doc.page_count, salida.stat().st_size / 1e6
    doc.close()
    corta = (salida.relative_to(REND.parent)
             if salida.is_relative_to(REND.parent) else salida)
    print(f"\n  → {corta}  ·  {total} páginas  ·  {mb:.1f} MB")
    for etiqueta, fondos, _ in piezas:
        print(f"     {etiqueta}: {len(fondos)} pág.")
    print(f"  máscaras suaves de luminosidad: {n}   "
          f"{'✅ ninguna — sin transparencia viva' if n == 0 else '🔴 quedan'}")


if __name__ == "__main__":
    main()
