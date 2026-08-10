#!/usr/bin/env python3
"""Mide los dpi REALES de cada imagen del menú, contra la caja donde se imprime.

El tamaño en píxeles de un archivo no dice nada: lo que manda es cuántos
píxeles del original caen dentro de la caja impresa. Con `object-fit: cover`
—que es lo que usan casi todas las fotos del menú— una parte del archivo se
recorta en pantalla, así que el dpi efectivo es **menor** que el que sugiere el
tamaño del archivo.

    dpi = 96 / escala        escala = px CSS mostrados / px del archivo

Recorre `render/menu-completo.html` con Playwright, mide TODO lo que pinta un
mapa de bits —`<img>` y `background-image`— y lo ordena de peor a mejor.

    python3 render/auditar_resolucion.py            # informe en pantalla
    python3 render/auditar_resolucion.py --json     # + informe a output/

Los SVG no se miden: son vectores y no se pixelan nunca.
"""
from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from urllib.parse import unquote, urlparse

from playwright.async_api import async_playwright

REND = Path(__file__).parent
RAIZ = REND.parent
SRC = REND / "menu-completo.html"
OUT = RAIZ / "output"

MINIMO = 300          # dpi de imprenta
HOLGURA = 320         # objetivo con margen, por si la caja crece

JS = r"""
() => {
  const salida = [];
  const pagina = (el) => {
    const p = el.closest('section.page');
    if (!p) return -1;
    return [...document.querySelectorAll('section.page')].indexOf(p);
  };
  for (const img of document.images) {
    const r = img.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) continue;
    const cs = getComputedStyle(img);
    salida.push({
      tipo: 'img', src: img.currentSrc || img.src,
      nat_w: img.naturalWidth, nat_h: img.naturalHeight,
      box_w: r.width, box_h: r.height,
      fit: cs.objectFit, pagina: pagina(img),
      clase: img.className || '', filtro: cs.filter,
    });
  }
  for (const el of document.querySelectorAll('*')) {
    const cs = getComputedStyle(el);
    const bg = cs.backgroundImage;
    if (!bg || bg === 'none') continue;
    for (const m of bg.matchAll(/url\((["']?)(.*?)\1\)/g)) {
      const url = m[2];
      if (!url || url.startsWith('data:')) continue;
      const r = el.getBoundingClientRect();
      if (r.width < 1 || r.height < 1) continue;
      salida.push({
        tipo: 'bg', src: url, nat_w: 0, nat_h: 0,
        box_w: r.width, box_h: r.height,
        fit: cs.backgroundSize, pagina: pagina(el),
        clase: el.className || '',
      });
    }
  }
  return salida;
}
"""


def ruta_local(src: str) -> Path | None:
    p = urlparse(src)
    if p.scheme not in ("file", ""):
        return None
    return Path(unquote(p.path))


def dpi_efectivo(nat_w, nat_h, box_w, box_h, fit) -> float:
    """px del archivo por pulgada impresa. 96 px CSS = 1 pulgada."""
    if not nat_w or not nat_h:
        return 0.0
    dx, dy = 96 * nat_w / box_w, 96 * nat_h / box_h
    if fit in ("cover", "auto") or "cover" in str(fit):
        return min(dx, dy)      # cover recorta: manda el eje que se estira más
    if "contain" in str(fit):
        return max(dx, dy)
    return min(dx, dy)          # fill / none: el peor eje


async def recoger():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 2000, "height": 1400})
        await pg.goto(SRC.as_uri())
        await pg.wait_for_function(
            "() => [...document.images].every(i => i.complete)", timeout=90000)
        await pg.wait_for_timeout(800)
        datos = await pg.evaluate(JS)
        await b.close()
    return datos


def auditar_pdf(assets):
    """Lo mismo, pero dentro de output/menu-completo.pdf.

    Medir los assets no basta: si el generador reescalara las fotos al meterlas
    en el PDF, el menú saldría pixelado aunque los archivos estén perfectos.
    Aquí se mira lo que de verdad va a ir a la plancha.

    ⚠️ Un PDF de Chromium lleva TRES clases de mapa de bits, y confundirlas
    lleva a dar por rota una página que está bien:
      · **las fotos** — los archivos de `assets/`, incrustados tal cual. Se
        reconocen porque su tamaño en píxeles coincide con el del archivo.
      · **las capas rasterizadas** — cualquier elemento con un `filter` CSS.
        Chromium no sabe escribirlo en vector, así que lo convierte en mapa de
        bits a un máximo de ~300 dpi. En este menú son las sombras, y una
        sombra no tiene detalle que perder. **Por eso ninguna foto puede
        llevar `filter` encima** (§6.66): si lo lleva, deja de incrustarse y
        pasa a ser una de estas.
      · **los inline** (`xref 0`) — degradados y scrims, a 72 dpi. Igual: sin
        detalle.
    """
    import fitz
    pdf = OUT / "menu-completo.pdf"
    if not pdf.exists():
        print("\n  (sin output/menu-completo.pdf — corre render/build_pdf.py)")
        return
    # Huella de los archivos que la web pinta: (ancho, alto) en píxeles.
    # Varias fotos comparten medidas —los derivados salen todos de la misma
    # plantilla—, así que la huella identifica el ARCHIVO solo cuando es única.
    huellas = {}
    for a in assets:
        huellas.setdefault((a["nat_w"], a["nat_h"]), set()).add(a["archivo"])
    doc = fitz.open(pdf)
    fotos, capas, efectos = [], [], []
    for i, pg in enumerate(doc):
        for im in pg.get_image_info(xrefs=True):
            b = im["bbox"]
            w_pulg, h_pulg = (b[2] - b[0]) / 72, (b[3] - b[1]) / 72
            if w_pulg < 0.2 or h_pulg < 0.2:
                continue
            dpi = min(im["width"] / w_pulg, im["height"] / h_pulg)
            candidatos = huellas.get((im["width"], im["height"]))
            if not candidatos:
                nombre = ""
            elif len(candidatos) == 1:
                nombre = next(iter(candidatos))
            else:
                nombre = f"uno de {len(candidatos)}: " + ", ".join(sorted(candidatos)[:2]) + "…"
            fila = (dpi, i + 1, im["width"], im["height"],
                    w_pulg * 25.4, h_pulg * 25.4, nombre)
            if not im.get("xref"):
                efectos.append(fila)
            elif nombre:
                fotos.append(fila)
            else:
                capas.append(fila)
    fotos.sort()
    print(f"\n  ── DENTRO DEL PDF ──\n")
    print(f"  {'dpi':>6}  {'pág':>3}  {'píxeles incrustados':>21}  {'caja dibujada':>17}"
          f"  archivo")
    for dpi, p, w, h, wm, hm, nombre in fotos:
        marca = "🔴" if dpi < MINIMO else "  "
        print(f"{marca}{dpi:>6.0f}  {p:>3}  {w:>9}×{h:<11}  {wm:>6.1f}×{hm:<6.1f} mm"
              f"  {nombre}")
    bajas = [f for f in fotos if f[0] < MINIMO]
    print(f"\n  {len(fotos)} fotos incrustadas · {len(bajas)} bajo {MINIMO} dpi")
    if capas:
        print(f"  {len(capas)} capas rasterizadas por un `filter` CSS "
              f"({min(c[0] for c in capas):.0f}–{max(c[0] for c in capas):.0f} dpi) "
              f"— son sombras, sin detalle que perder")
    if efectos:
        peor = min(e[0] for e in efectos)
        print(f"  {len(efectos)} degradados y scrims en línea "
              f"(el peor a {peor:.0f} dpi) — íd.")

    # Las fotos que llevan `filter` NO se incrustan: Chromium las convierte en
    # una capa de mapa de bits topada en ~300 dpi. Cumplen el mínimo, pero
    # pierden todo el margen que tenía el archivo, y conviene verlo escrito.
    con_filtro = [a for a in assets if a.get("filtro", "none") != "none"]
    if con_filtro:
        print(f"\n  ⚠️ {len(con_filtro)} fotos llevan `filter` CSS y por eso "
              f"Chromium las rasteriza (tope ~300 dpi) en vez de incrustarlas:")
        for a in con_filtro:
            # La capa que le corresponde es la de su misma página que ENVUELVE
            # su caja (crece con la sombra) y es la más ceñida de las que la
            # envuelven. Así se informa el dpi medido, no el tope teórico.
            cw, ch = a["caja_mm"]
            # Sin holgura: la capa siempre es MAYOR que la caja (la sombra
            # se sale). Con holgura, el perrito casaba con la capa del pato.
            dentro = [c for c in capas if c[1] == a["pagina"]
                      and c[4] >= cw and c[5] >= ch]
            real = f"{min(dentro, key=lambda c: c[4] * c[5])[0]:.0f}" if dentro else "≤300"
            print(f"     pág {a['pagina']:>2}  {a['archivo']:<40} "
                  f"{a['dpi']:>5} dpi en el archivo → {real:>4} en el PDF")
        print("     Se arregla como §6.66: la sombra, a su propia capa. Un "
              "ajuste de color hay que hornearlo en el archivo.")
    return len(bajas)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true", help="escribe output/auditoria-resolucion.json")
    ap.add_argument("--pdf", action="store_true",
                    help="audita además las imágenes ya incrustadas en el PDF")
    args = ap.parse_args()

    datos = asyncio.run(recoger())

    filas, svg, faltan = [], [], []
    from PIL import Image
    for d in datos:
        ruta = ruta_local(d["src"])
        nombre = ruta.name if ruta else d["src"]
        if nombre.lower().endswith(".svg"):
            svg.append(nombre)
            continue
        if ruta is None or not ruta.exists():
            faltan.append(nombre)
            continue
        if not d["nat_w"]:
            with Image.open(ruta) as im:
                d["nat_w"], d["nat_h"] = im.size
        dpi = dpi_efectivo(d["nat_w"], d["nat_h"], d["box_w"], d["box_h"], d["fit"])
        filas.append({
            "archivo": nombre,
            "ruta": str(ruta.relative_to(RAIZ)) if ruta.is_relative_to(RAIZ) else str(ruta),
            "pagina": d["pagina"] + 1,
            "tipo": d["tipo"],
            "clase": " ".join(str(d["clase"]).split()[:2]),
            "px": f'{d["nat_w"]}×{d["nat_h"]}',
            "nat_w": d["nat_w"], "nat_h": d["nat_h"],
            "caja_mm": (round(d["box_w"] / 3.779528, 1), round(d["box_h"] / 3.779528, 1)),
            "fit": d["fit"],
            "filtro": d.get("filtro", "none"),
            "dpi": round(dpi),
        })

    filas.sort(key=lambda f: f["dpi"])
    bajas = [f for f in filas if f["dpi"] < MINIMO]
    justas = [f for f in filas if MINIMO <= f["dpi"] < HOLGURA]

    print(f"\n  {len(filas)} imágenes de mapa de bits · {len(svg)} SVG (vectores, no se miden)")
    if faltan:
        print(f"  ⚠️ {len(faltan)} sin archivo local: {', '.join(sorted(set(faltan)))}")
    print(f"\n  {'dpi':>5}  {'pág':>3}  {'archivo':<40}{'píxeles':>12}  "
          f"{'caja impresa':>16}  fit")
    print("  " + "─" * 96)
    for f in filas:
        marca = "🔴" if f["dpi"] < MINIMO else ("🟡" if f["dpi"] < HOLGURA else "  ")
        cw, ch = f["caja_mm"]
        print(f"{marca}{f['dpi']:>5}  {f['pagina']:>3}  {f['archivo']:<40}{f['px']:>12}  "
              f"{cw:>6.1f}×{ch:<6.1f}mm  {f['fit']}")

    print(f"\n  🔴 bajo {MINIMO} dpi: {len(bajas)}   🟡 entre {MINIMO} y {HOLGURA}: {len(justas)}"
          f"   ✅ ≥{HOLGURA}: {len(filas) - len(bajas) - len(justas)}")

    if args.json:
        OUT.mkdir(exist_ok=True)
        (OUT / "auditoria-resolucion.json").write_text(
            json.dumps(filas, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  → output/auditoria-resolucion.json")

    if args.pdf:
        bajas += [None] * auditar_pdf(filas)

    return 1 if bajas else 0


if __name__ == "__main__":
    raise SystemExit(main())
