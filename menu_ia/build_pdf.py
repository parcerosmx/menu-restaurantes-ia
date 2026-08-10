#!/usr/bin/env python3
"""Genera output/menu-completo.pdf desde render/menu-completo.html.

`render.py` es el generador viejo: apunta a `menu.html` (la maqueta de 8
páginas de julio, superada) y a un formato carta que ya no es el del proyecto.
Este es el del menú vigente: 14 páginas de 192 × 285 mm con sangrado, en el
mismo orden que manda `spreads-activos.json`.

⚠️ **No es el PDF de imprenta.** Sale en RGB y con las fuentes incrustadas por
Chromium; la conversión a CMYK y el control de tintas es otro paso
(`preparar_imprenta.py`) y va cuando el dueño lo confirme. Este PDF es para
revisar el menú entero en una sola pieza.

    python3 render/build_menu.py && python3 render/build_pdf.py
"""
import asyncio
import json
from pathlib import Path

from playwright.async_api import async_playwright

import idiomas

REND = Path(__file__).parent
IDIOMA = idiomas.pedido()
SRC = idiomas.ruta(REND / "menu-completo.html", IDIOMA)
OUT = idiomas.ruta(REND.parent / "output" / "menu-completo.pdf", IDIOMA)


async def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    activos = json.loads(
        idiomas.ruta(REND / "spreads-activos.json", IDIOMA).read_text(encoding="utf-8"))

    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page()
        await pg.goto(SRC.as_uri())
        # Igual que shot_spreads.py: las fotos son pesadas y una que no haya
        # decodificado sale en blanco en el PDF, sin avisar.
        await pg.wait_for_function(
            "() => [...document.images].every(i => i.complete && i.naturalWidth > 0)",
            timeout=120000)
        await pg.evaluate("document.fonts.ready")
        await pg.emulate_media(media="print")
        await pg.wait_for_timeout(1500)
        await pg.pdf(path=str(OUT), print_background=True, prefer_css_page_size=True)
        await b.close()

    mb = OUT.stat().st_size / 1e6
    print(f"→ {OUT.relative_to(REND.parent)}  ·  {len(activos) * 2} páginas esperadas"
          f"  ·  {mb:.1f} MB")


if __name__ == "__main__":
    asyncio.run(main())
