#!/usr/bin/env python3
"""Impone las 16 páginas en las 8 caras que se imprimen, para grapa (saddle stitch).

**Qué es imponer.** El menú se lee 1, 2, 3… pero no se imprime así. Son **4
hojas** dobladas por la mitad y grapadas por el lomo: cada hoja lleva 4 páginas,
dos por cara, y **no son consecutivas**. La regla es que en cada cara las dos
páginas suman siempre 17 (nº de páginas + 1):

    hoja 1 (fuera)  exterior 16 ǀ 1     interior  2 ǀ 15
    hoja 2          exterior 14 ǀ 3     interior  4 ǀ 13
    hoja 3          exterior 12 ǀ 5     interior  6 ǀ 11
    hoja 4 (centro) exterior 10 ǀ 7     interior  8 ǀ 9

⚠️ **Esto NO es el archivo que pide la mayoría de imprentas.** Casi todas
prefieren las páginas sueltas en orden de lectura y hacen ellas la imposición
en su RIP, porque depende de su máquina, su papel y su compensación de
desplazamiento. Entregar esto cuando esperaban orden de lectura sale mal.
Se genera como **alternativa**, para poder enseñárselo y que elijan.

**Sangrado en el lomo: no lo hay, y es a propósito.** El lomo es un DOBLEZ, no
un corte. Cada página fuente mide 192 × 285 mm (186 × 279 de página final + 3 mm
de sangre por lado); al montarla se le recorta la sangre del lado interior y las
dos páginas se juntan por su línea de corte. La cara queda en **378 × 285 mm**:
3 + 186 + 186 + 3 de ancho, y arriba y abajo la sangre intacta.

**Lo que este script NO hace, y hay que decirlo:** no aplica compensación de
desplazamiento (*creep*). Con 16 páginas, las de dentro sobresalen por el corte
delantero y se les recorta más; la corrección depende del **grosor del papel**,
que es dato de la imprenta. Si la hacen ellos, va incluida. Si insisten en el
archivo impuesto, hay que pedirles el gramaje y añadirla aquí.

    python3 render/imponer_pdf.py
    python3 render/imponer_pdf.py --entrada output/menu-completo-plano.pdf
"""
from __future__ import annotations

import argparse
from pathlib import Path

import fitz

# La raíz es la del CLIENTE, no la del paquete: aquí están su HTML, su
# CSS y sus datos. Deducirla de `__file__` daba site-packages.
from .proyecto import RAIZ as REND
from .proyecto import SALIDA as OUT

MM = 72 / 25.4
# Fuente única en `formato.py`. Los nombres locales se conservan para no tocar
# el resto del script.
from .formato import CORTE_MM as PAGINA_FINAL_MM  # noqa: E402
from .formato import SANGRADO_MM as SANGRE_MM     # noqa: E402


def parejas(total: int):
    """Las caras, de la hoja de fuera hacia el centro.

    Devuelve (izquierda, derecha) con numeración 1..total. La suma de cada
    pareja es siempre total + 1: es lo que hace que al doblar y grapar salga
    el orden de lectura.
    """
    if total % 4:
        raise SystemExit(f"{total} páginas: para grapa tiene que ser múltiplo de 4")
    caras = []
    izq, der = total, 1
    while izq > der:
        caras.append((izq, der))            # cara exterior de la hoja
        izq, der = der + 1, izq - 1
        if izq > der:
            break
        caras.append((izq, der))            # cara interior de la misma hoja
        izq, der = der - 1, izq + 1
    return caras


def imponer(entrada: Path, salida: Path):
    src = fitz.open(entrada)
    total = src.page_count
    caras = parejas(total)

    ancho_final, alto_final = PAGINA_FINAL_MM
    w = (SANGRE_MM + ancho_final * 2 + SANGRE_MM) * MM
    h = (SANGRE_MM + alto_final + SANGRE_MM) * MM
    media = (SANGRE_MM + ancho_final) * MM      # dónde cae el doblez

    doc = fitz.open()
    print(f"  {'cara':>5}  {'hoja':>5}  {'lado':<9} páginas")
    for n, (izq, der) in enumerate(caras):
        pagina = doc.new_page(width=w, height=h)
        origen = src[izq - 1].rect
        # A la izquierda se le quita la sangre del borde DERECHO (el del lomo);
        # a la derecha, la del IZQUIERDO. Las de fuera se conservan.
        pagina.show_pdf_page(
            fitz.Rect(0, 0, media, h), src, izq - 1,
            clip=fitz.Rect(0, 0, origen.width - SANGRE_MM * MM, origen.height))
        pagina.show_pdf_page(
            fitz.Rect(media, 0, w, h), src, der - 1,
            clip=fitz.Rect(SANGRE_MM * MM, 0, origen.width, origen.height))
        hoja, lado = n // 2 + 1, ("exterior" if n % 2 == 0 else "interior")
        print(f"  {n + 1:>5}  {hoja:>5}  {lado:<9} {izq:>2} ǀ {der:<2}")

    doc.save(salida, deflate=True, garbage=4)
    doc.close()
    src.close()
    return len(caras), w / MM, h / MM


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrada", default=str(OUT / "menu-completo-plano.pdf"))
    ap.add_argument("--salida", default=str(OUT / "menu-imposicion-grapa.pdf"))
    args = ap.parse_args()

    entrada = Path(args.entrada)
    if not entrada.exists():
        raise SystemExit(f"falta {entrada} — corre render/build_pdf_plano.py")
    salida = Path(args.salida)
    n, w, h = imponer(entrada, salida)
    print(f"\n  → {salida.relative_to(REND.parent)}  ·  {n} caras de "
          f"{w:.0f} × {h:.0f} mm  ·  {salida.stat().st_size / 1e6:.1f} MB")
    print("  ⚠️ sin compensación de desplazamiento: depende del gramaje, "
          "y ese dato es de la imprenta.")


if __name__ == "__main__":
    main()
