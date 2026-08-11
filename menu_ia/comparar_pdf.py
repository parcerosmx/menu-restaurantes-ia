#!/usr/bin/env python3
"""Compara el PDF contra los PNG de referencia, doble página por doble página.

Los PNG salen de `shot_spreads.py` (Chromium, media `screen`) y el PDF de
`build_pdf.py` (Chromium, media `print`). Son dos rutas distintas del mismo
motor, así que **tienen que dar la misma página** — y si no la dan, es un
error de maquetación que solo se ve en el PDF, que es lo que va a imprenta.

Qué mide, y por qué así:

- **Diferencia media** sobre la luminancia, en niveles de 0 a 255. El
  antialiasing y el submuestreo de fotos del PDF nunca dan 0; lo que importa
  es que la cifra sea baja y esté repartida, no concentrada.
- **% de píxeles con diferencia > 32.** Este es el número que delata un
  problema real: texto desplazado, una foto que no cargó, un bloque movido.
  Un desfase tipográfico deja una diferencia grande en muy pocos píxeles;
  un bloque movido la deja en muchos.
- **Mapa de calor por bandas.** Parte la doble página en una rejilla y dice
  en qué zona está la diferencia, para no tener que mirar el diff a ojo.

Escribe `output/diff/` con, por cada doble página, el PNG, el PDF rasterizado
al mismo tamaño y el mapa de diferencias.

    python3 render/comparar_pdf.py
    python3 render/comparar_pdf.py --umbral 24
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import fitz
import numpy as np
from PIL import Image

# La raíz es la del CLIENTE, no la del paquete: aquí están su HTML, su
# CSS y sus datos. Deducirla de `__file__` daba site-packages.
from .proyecto import RAIZ as REND
RAIZ = REND.parent
PDF = RAIZ / "output" / "menu-completo.pdf"
OUT = RAIZ / "output"
DIFF = OUT / "diff"

REJILLA = (6, 4)          # columnas × filas del mapa de calor
UMBRAL = 32               # niveles de luma a partir de los cuales cuenta


def spreads():
    m = json.loads((REND / "spreads-activos.json").read_text(encoding="utf-8"))
    return [(i, s["slug"], OUT / f"menu-doble-pagina-{i + 1}-{s['slug']}.png")
            for i, s in enumerate(m)]


def pdf_spread(doc, i: int, tam: tuple[int, int]) -> Image.Image:
    """Rasteriza las dos páginas del pliego i y las pega como el PNG."""
    izq, der = doc[i * 2], doc[i * 2 + 1]
    escala = tam[0] / (izq.rect.width + der.rect.width)
    partes = []
    for p in (izq, der):
        pix = p.get_pixmap(matrix=fitz.Matrix(escala, escala))
        partes.append(Image.frombytes("RGB", (pix.width, pix.height), pix.samples))
    ancho = sum(p.width for p in partes)
    alto = max(p.height for p in partes)
    lienzo = Image.new("RGB", (ancho, alto), "white")
    lienzo.paste(partes[0], (0, 0))
    lienzo.paste(partes[1], (partes[0].width, 0))
    return lienzo.resize(tam, Image.LANCZOS) if lienzo.size != tam else lienzo


def mapa_calor(d: np.ndarray, umbral: int):
    """% de píxeles sobre el umbral por celda de la rejilla."""
    cols, filas = REJILLA
    h, w = d.shape
    out = []
    for r in range(filas):
        fila = []
        for c in range(cols):
            celda = d[r * h // filas:(r + 1) * h // filas,
                      c * w // cols:(c + 1) * w // cols]
            fila.append(float((celda > umbral).mean() * 100))
        out.append(fila)
    return out


def peores_zonas(d: np.ndarray, umbral: int, n: int, celda_px: int = 64):
    """Las n celdas con más diferencia, ya fusionadas por vecindad.

    Sirve para mirar el problema, no la media: una celda con el 60 % de
    píxeles distintos es un bloque movido; el antialiasing reparte y no pasa
    del 10 % en ninguna.
    """
    h, w = d.shape
    fh, fw = h // celda_px, w // celda_px
    rejilla = np.zeros((fh, fw))
    for r in range(fh):
        for c in range(fw):
            rejilla[r, c] = (d[r * celda_px:(r + 1) * celda_px,
                               c * celda_px:(c + 1) * celda_px] > umbral).mean() * 100
    zonas, usada = [], np.zeros_like(rejilla, dtype=bool)
    for _ in range(n):
        rejilla_lib = np.where(usada, -1, rejilla)
        r, c = np.unravel_index(int(np.argmax(rejilla_lib)), rejilla.shape)
        if rejilla_lib[r, c] <= 0:
            break
        # crece mientras las vecinas también estén mal
        r0 = r1 = r
        c0 = c1 = c
        for _ in range(6):
            for rr in range(max(0, r0 - 1), min(fh, r1 + 2)):
                for cc in range(max(0, c0 - 1), min(fw, c1 + 2)):
                    if rejilla[rr, cc] > rejilla[r, c] * 0.45:
                        r0, r1 = min(r0, rr), max(r1, rr)
                        c0, c1 = min(c0, cc), max(c1, cc)
        usada[r0:r1 + 1, c0:c1 + 1] = True
        zonas.append((float(rejilla[r, c]),
                      (c0 * celda_px, r0 * celda_px,
                       (c1 + 1) * celda_px, (r1 + 1) * celda_px)))
    return zonas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--umbral", type=int, default=UMBRAL)
    ap.add_argument("--zonas", type=int, default=0,
                    help="además, saca las N peores zonas de cada doble página "
                         "como recorte PNG-sobre-PDF a output/diff/zonas/")
    ap.add_argument("--sin-imagenes", action="store_true",
                    help="solo las cifras, no escribe output/diff/")
    args = ap.parse_args()

    if not PDF.exists():
        raise SystemExit("falta output/menu-completo.pdf — corre render/build_pdf.py")
    doc = fitz.open(PDF)
    lista = spreads()
    if doc.page_count != len(lista) * 2:
        print(f"  ⚠️ el PDF tiene {doc.page_count} páginas y se esperaban "
              f"{len(lista) * 2}")
    if not args.sin_imagenes:
        DIFF.mkdir(parents=True, exist_ok=True)

    print(f"\n  {'doble página':<16}{'dif. media':>12}{'> ' + str(args.umbral):>10}"
          f"{'peor celda':>12}   dónde")
    print("  " + "─" * 72)
    peor_global = 0.0
    for i, slug, ruta_png in lista:
        if not ruta_png.exists():
            print(f"  {slug:<16}  falta el PNG de referencia")
            continue
        png = Image.open(ruta_png).convert("RGB")
        pdf = pdf_spread(doc, i, png.size)

        a = np.asarray(png.convert("L"), dtype=np.int16)
        b = np.asarray(pdf.convert("L"), dtype=np.int16)
        d = np.abs(a - b)
        media = float(d.mean())
        pct = float((d > args.umbral).mean() * 100)
        calor = mapa_calor(d, args.umbral)
        peor = max(max(f) for f in calor)
        peor_global = max(peor_global, pct)
        r, c = next((r, c) for r, f in enumerate(calor)
                    for c, v in enumerate(f) if v == peor)
        lado = "izq" if c < REJILLA[0] / 2 else "der"
        print(f"  {slug:<16}{media:>12.2f}{pct:>9.2f}%{peor:>11.1f}%   "
              f"fila {r + 1}/{REJILLA[1]}, col {c + 1}/{REJILLA[0]} ({lado})")

        if not args.sin_imagenes:
            pdf.save(DIFF / f"{i + 1}-{slug}-pdf.png")
            heat = np.clip(d * 4, 0, 255).astype(np.uint8)
            Image.fromarray(255 - heat).save(DIFF / f"{i + 1}-{slug}-diff.png")

        if args.zonas:
            zdir = DIFF / "zonas"
            zdir.mkdir(parents=True, exist_ok=True)
            pxmm = png.width / 384.0
            for k, (val, caja) in enumerate(
                    peores_zonas(d, args.umbral, args.zonas), 1):
                a, b = png.crop(caja), pdf.crop(caja)
                par = Image.new("RGB", (a.width, a.height * 2 + 8), "white")
                par.paste(a, (0, 0))
                par.paste(b, (0, a.height + 8))
                par.save(zdir / f"{i + 1}-{slug}-z{k}.png")
                print(f"      z{k}  {val:5.1f}%  en x{caja[0] / pxmm:6.1f} "
                      f"y{caja[1] / pxmm:6.1f} mm   (PNG arriba, PDF abajo)")

    print(f"\n  peor doble página: {peor_global:.2f}% de píxeles sobre el umbral")
    if not args.sin_imagenes:
        print(f"  → output/diff/\n")


if __name__ == "__main__":
    main()
