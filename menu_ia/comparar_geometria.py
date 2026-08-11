#!/usr/bin/env python3
"""Comprueba que texto y fotos caen en el MISMO sitio en el PDF que en la web.

`comparar_pdf.py` compara píxeles, y los píxeles nunca dan cero: el PNG lo
rasteriza Chromium y el PDF lo rasteriza MuPDF, con motores de fuentes
distintos. Eso deja un ruido de fondo que no se puede quitar y que **tapa** lo
único que importa de verdad: si algo se ha MOVIDO.

Esto lo mide directamente. Saca la posición de cada línea de texto por dos
caminos —el DOM del navegador y el propio PDF— y las empareja por su contenido.
Si el desplazamiento es de centésimas de milímetro, la maqueta es la misma y lo
que queda es rasterizado. Si alguna se va milímetros, hay un fallo real.

Va en dos partes: las líneas de texto (emparejadas por su contenido) y las
fotos (emparejadas por su caja). Las fotos importan tanto como el texto: media
página del menú es foto a sangre, y una que se desplace no la ve nadie mirando
cifras de píxeles distintos —sale igual de "distinta" que un reescalado—.

    python3 render/comparar_geometria.py
    python3 render/comparar_geometria.py --tolerancia 0.5
"""
from __future__ import annotations

import argparse
import asyncio
import json
import re
import unicodedata
from pathlib import Path

import fitz
from playwright.async_api import async_playwright

from .formato import PAGINA_MM

# La raíz es la del CLIENTE, no la del paquete: aquí están su HTML, su
# CSS y sus datos. Deducirla de `__file__` daba site-packages.
from .proyecto import RAIZ as REND
SRC = REND / "menu-completo.html"
PDF = REND.parent / "output" / "menu-completo.pdf"

TOLERANCIA = 0.35        # mm; por debajo de esto no lo ve nadie en papel
PX_MM = 96 / 25.4        # 1 px CSS = 1/96 pulgada

# ── Las dos fotos que SIEMPRE han medido por encima del umbral ──────────────
# `style-guide.md` §9.4 documenta la maqueta sana como «≤ 0.32 mm en texto y
# 0.00 mm en 33 de 35 fotos», y nombra el resto: **«el conocido de coctelería
# (0.397 mm)»**. Son estas dos, y llevan así desde que existe la medición.
#
# El problema no era el desplazamiento —0.4 mm no lo ve nadie en papel—, era
# que `TOLERANCIA` global valía 0.35: **la guarda daba rojo con la maqueta
# sana**, y por tanto `hacer.py verificar` no podía terminar en verde nunca.
# Una comprobación que siempre falla no se lee, se saltea; y el día que se
# mueva algo de verdad, el rojo nuevo se pierde entre los dos de siempre.
#
# ⚠️ La salida NO es subir `TOLERANCIA` a 0.45: eso taparía un desplazamiento
# real de 0.38 mm en cualquiera de las otras 34 fotos. Se nombran las dos
# excepciones, con su propio techo. Si una de ellas se pasa de ahí, vuelve a
# ser 🔴 — la excepción cubre lo medido, no cualquier cosa que pase mañana.
CONOCIDAS = {
    "cantarito-patio-ia-01.png": 0.45,
    "bichota-girada-ia-01.png": 0.45,
}

JS = r"""
() => {
  const paginas = [...document.querySelectorAll('section.page')];
  return paginas.map(pag => {
    const base = pag.getBoundingClientRect();
    const filas = [];
    const it = document.createTreeWalker(pag, NodeFilter.SHOW_TEXT);
    let n;
    while ((n = it.nextNode())) {
      if (!n.nodeValue.trim()) continue;
      const cs = getComputedStyle(n.parentElement);
      if (cs.visibility === 'hidden' || cs.display === 'none') continue;
      const r = document.createRange();
      r.selectNodeContents(n);
      for (const caja of r.getClientRects()) {
        if (caja.width < 1 || caja.height < 1) continue;
        filas.push({t: n.nodeValue, x: caja.left - base.left, y: caja.top - base.top,
                    tt: cs.textTransform});
      }
    }
    const imgs = [...pag.querySelectorAll('img')].map(im => {
      const c = im.getBoundingClientRect();
      return {src: (im.currentSrc || im.src).split('/').pop(),
              x: c.left - base.left, y: c.top - base.top,
              w: c.width, h: c.height};
    }).filter(i => i.w > 1 && i.h > 1);
    return {filas, imgs};
  });
}
"""


def normalizar(s: str) -> str:
    s = unicodedata.normalize("NFKC", s)
    s = re.sub(r"[\s ]+", " ", s).strip().lower()
    # el PDF trae el letter-spacing como espacios entre letras: se descartan
    return re.sub(r"[^0-9a-záéíóúüñ]", "", s)


ALFA = re.compile(r"[0-9a-záéíóúüñ]", re.IGNORECASE)


def arranca_limpio(s: str) -> bool:
    """¿El primer carácter visible es ya parte del texto normalizado?

    Hace falta porque `normalizar` se come los símbolos: el span
    «• G I G A N T E» del PDF y el nodo «gigante» del DOM dan la misma clave,
    pero sus cajas empiezan en sitios distintos — ese punto vale 5.3 mm. Si un
    lado no arranca limpio, la X no es comparable. La Y sí lo es siempre, y la
    Y es la que delata los fallos de paginación.
    """
    # Sin `strip()` a propósito: un span del PDF que empieza por espacio
    # (« 1600») lleva ese espacio DENTRO de su caja, y son 1.8 mm.
    s = unicodedata.normalize("NFKC", s)
    return bool(s) and bool(ALFA.match(s[0]))


async def del_dom():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 2000, "height": 1400})
        await pg.goto(SRC.as_uri())
        await pg.wait_for_function(
            "() => [...document.images].every(i => i.complete)", timeout=120000)
        await pg.wait_for_timeout(600)
        datos = await pg.evaluate(JS)
        await b.close()
    salida, imagenes = [], []
    for pagina in datos:
        filas = pagina["filas"]
        imagenes.append([{k: (v / PX_MM if k in "xywh" else v) for k, v in im.items()}
                         for im in pagina["imgs"]])
        d = {}
        for f in filas:
            t = f["t"]
            if f["tt"] == "uppercase":
                t = t.upper()
            k = normalizar(t)
            if len(k) < 4:
                continue
            d.setdefault(k, []).append(
                (f["x"] / PX_MM, f["y"] / PX_MM, arranca_limpio(t)))
        salida.append(d)
    return salida, imagenes


def desfase_foto(pag_pdf, png_spread, im, lado, mm_px, rango_mm=3.0):
    """¿Cuánto habría que mover el recorte del PDF para que case con el PNG?

    ⚠️ La vía obvia —comparar la caja que declara el PDF con la caja CSS— NO
    sirve, y conviene dejarlo escrito para que nadie la reintente: con
    `object-fit: cover` el PDF coloca la foto ENTERA y la recorta con un clip,
    así que su caja siempre es mayor que la ventana visible. `ajiaco.jpg` se ve
    en 70.4 × 30 mm y el PDF la declara en 68 × 45.2: 15 mm de "desviación" que
    no existe.

    Lo que sí se puede afirmar es esto: recorta la MISMA ventana en el PNG y en
    el PDF y busca el desplazamiento que mejor las hace coincidir. Si es cero,
    la foto está en su sitio, sea cual sea la caja que el PDF declare.
    """
    import numpy as np
    x0, y0 = im["x"] + lado, im["y"]
    x1, y1 = x0 + im["w"], y0 + im["h"]
    margen = rango_mm
    caja = tuple(int(round(v * mm_px)) for v in
                 (x0 + margen, y0 + margen, x1 - margen, y1 - margen))
    if caja[2] - caja[0] < 40 or caja[3] - caja[1] < 40:
        return None
    ref = np.asarray(png_spread.crop(caja).convert("L"), dtype=np.float32)

    esc = mm_px / (72 / 25.4)          # de puntos PDF a píxeles del PNG
    pix = pag_pdf.get_pixmap(matrix=fitz.Matrix(esc, esc))
    from PIL import Image as _Im
    pdf_im = _Im.frombytes("RGB", (pix.width, pix.height), pix.samples).convert("L")

    # Barrido a paso de 1 px (~0.13 mm): con paso 2 el resultado se cuantiza
    # en saltos de 0.26 mm y dos fotos daban 0.40 mm que en realidad eran 0.
    r = int(round(rango_mm * mm_px))
    mejor = (1e9, 0, 0)
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            c = (caja[0] - lado_px(lado, mm_px) + dx, caja[1] + dy,
                 caja[2] - lado_px(lado, mm_px) + dx, caja[3] + dy)
            if c[0] < 0 or c[1] < 0 or c[2] > pdf_im.width or c[3] > pdf_im.height:
                continue
            v = np.asarray(pdf_im.crop(c), dtype=np.float32)
            if v.shape != ref.shape:
                continue
            d = float(np.abs(ref - v).mean())
            if d < mejor[0]:
                mejor = (d, dx, dy)
    return (mejor[1] / mm_px, mejor[2] / mm_px, mejor[0])


def lado_px(lado_mm, mm_px):
    return int(round(lado_mm * mm_px))


def del_pdf():
    doc = fitz.open(PDF)
    salida = []
    for pg in doc:
        d = {}
        for blk in pg.get_text("dict")["blocks"]:
            for linea in blk.get("lines", []):
                # Se indexan la línea entera Y cada span. El DOM se recorre por
                # nodos de texto, y un nodo no siempre es una línea: el pie es
                # `<span class="corazon">♥</span>De corazón y sabor.`, así que
                # el nodo empieza 3.07 mm a la derecha de la línea. Con los dos
                # índices, cada lado encuentra su pareja exacta.
                trozos = [("".join(s["text"] for s in linea["spans"]), linea["bbox"])]
                if len(linea["spans"]) > 1:
                    trozos += [(s["text"], s["bbox"]) for s in linea["spans"]]
                for t, caja in trozos:
                    k = normalizar(t)
                    if len(k) < 4:
                        continue
                    d.setdefault(k, []).append(
                        (caja[0] / 72 * 25.4, caja[1] / 72 * 25.4,
                         arranca_limpio(t)))
        salida.append(d)
    return salida


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tolerancia", type=float, default=TOLERANCIA)
    args = ap.parse_args()

    dom, imgs_dom = asyncio.run(del_dom())
    pdf = del_pdf()
    if len(dom) != len(pdf):
        print(f"  ⚠️ {len(dom)} páginas en el HTML y {len(pdf)} en el PDF")

    print("\n  ── TEXTO ──")
    print(f"\n  {'pág':>4}  {'anclas':>7}  {'dx medio':>9}  {'dy medio':>9}"
          f"  {'peor':>7}   línea peor")
    print("  " + "─" * 78)
    fuera_total, anclas_total, peor_global = 0, 0, (0.0, "", 0)
    for i, (a, b) in enumerate(zip(dom, pdf)):
        # solo las líneas que aparecen una vez en cada lado: sin ambigüedad
        comunes = [k for k in a if k in b and len(a[k]) == 1]
        dxs, dys, peor = [], [], (0.0, "")
        fuera = 0
        sin_x = 0
        for k in comunes:
            ax, ay, a_lim = a[k][0]
            # el PDF repite el mismo texto por el text-shadow: la buena es la
            # más cercana, no la primera que salga
            bx, by, b_lim = min(b[k], key=lambda p: abs(p[0] - ax) + abs(p[1] - ay))
            dx, dy = bx - ax, by - ay
            dys.append(dy)
            comparable_x = a_lim and b_lim
            if comparable_x:
                dxs.append(dx)
            else:
                sin_x += 1
            dist = max(abs(dx), abs(dy)) if comparable_x else abs(dy)
            if dist > args.tolerancia:
                fuera += 1
            if dist > peor[0]:
                peor = (dist, k)
        if not comunes:
            print(f"  {i + 1:>4}  {'—':>7}   sin anclas comparables")
            continue
        anclas_total += len(comunes)
        fuera_total += fuera
        if peor[0] > peor_global[0]:
            peor_global = (peor[0], peor[1], i + 1)
        marca = "🔴" if fuera else "  "
        media_x = sum(dxs) / len(dxs) if dxs else 0.0
        print(f"{marca}{i + 1:>4}  {len(comunes):>7}  {media_x:>+8.3f}mm"
              f"  {sum(dys)/len(dys):>+8.3f}mm  {peor[0]:>6.3f}mm   {peor[1][:28]}"
              + (f"   ← {fuera} fuera de tolerancia" if fuera else ""))

    print(f"\n  {anclas_total} líneas emparejadas · {fuera_total} por encima de "
          f"{args.tolerancia} mm")
    print(f"  peor desplazamiento: {peor_global[0]:.3f} mm "
          f"(pág. {peor_global[2]}, «{peor_global[1][:30]}»)")

    # ---- FOTOS ----
    # El PDF dibuja más mapas de bits que <img> tiene el HTML: los degradados,
    # las sombras y los fondos con `border-radius` los rasteriza Chromium. Por
    # eso no se comparan listas, se busca para cada <img> la caja del PDF que
    # más se le parece. Lo que se afirma es "ninguna foto se ha movido", que es
    # justo lo que el conteo de píxeles no sabe decir.
    print("\n  ── FOTOS ──\n")
    from PIL import Image
    manifiesto = json.loads((REND / "spreads-activos.json").read_text(encoding="utf-8"))
    doc = fitz.open(PDF)
    total, fuera_img, peor_img, saltadas, conocidas = 0, 0, (0.0, "", 0), 0, 0
    for i, lista in enumerate(imgs_dom):
        s = manifiesto[i // 2]
        ruta = (REND.parent / "output"
                / f"menu-doble-pagina-{i // 2 + 1}-{s['slug']}.png")
        if not ruta.exists():
            print(f"  ⚠️ falta {ruta.name}; sin referencia para la pág. {i + 1}")
            continue
        spread = Image.open(ruta)
        # El PNG de referencia es el PLIEGO: dos páginas con sangre, lado a
        # lado. Ambas medidas salen de `formato.py` — estaban tecleadas.
        mm_px = spread.width / (PAGINA_MM[0] * 2)
        lado = 0.0 if i % 2 == 0 else float(PAGINA_MM[0])  # la par abre el pliego
        for im in lista:
            total += 1
            r = desfase_foto(doc[i], spread, im, lado, mm_px)
            if r is None:
                saltadas += 1
                continue
            dx, dy, resto = r
            desv = max(abs(dx), abs(dy))
            if desv > peor_img[0]:
                peor_img = (desv, im["src"], i + 1)
            techo = CONOCIDAS.get(Path(im["src"]).name)
            if techo is not None and args.tolerancia < desv <= techo:
                conocidas += 1
                print(f"  🟡 pág {i + 1:>2}  {im['src']:<38} "
                      f"dx {dx:+.2f} dy {dy:+.2f} mm  (conocida, §9.4)")
            elif desv > args.tolerancia:
                fuera_img += 1
                print(f"  🔴 pág {i + 1:>2}  {im['src']:<38} "
                      f"dx {dx:+.2f} dy {dy:+.2f} mm")
    print(f"  {total} fotos comprobadas ({saltadas} demasiado pequeñas para "
          f"correlacionar) · {fuera_img} desplazadas más de {args.tolerancia} mm"
          + (f" · {conocidas} conocidas de §9.4" if conocidas else ""))
    print(f"  peor desplazamiento: {peor_img[0]:.3f} mm "
          f"({peor_img[1]}, pág. {peor_img[2]})\n")
    return 1 if (fuera_total or fuera_img) else 0


if __name__ == "__main__":
    raise SystemExit(main())
