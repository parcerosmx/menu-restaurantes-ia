#!/usr/bin/env python3
"""Exporta cada DOBLE PÁGINA de render/menu-completo.html como PNG a output/.

Un PNG por sección = las 2 páginas enfrentadas (HERO izq. + listado der.),
que es como se ve el menú abierto.

⚠️ "doble página" NO es un "pliego" de imprenta: el pliego es la hoja física
y lleva 4 páginas. Glosario en CLAUDE.md.

Uso:

    python3 render/build_menu.py && python3 render/shot_spreads.py

No genera el PDF de imprenta — eso es otro paso (render/render.py).
"""
import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

import idiomas

REND = Path(__file__).parent
IDIOMA = idiomas.pedido()
SRC = idiomas.ruta(REND / "menu-completo.html", IDIOMA)
OUT = REND.parent / "output"

# La lista la manda build_menu.py (spreads-activos.json): así las secciones
# desactivadas —hoy el Brunch— no generan PNG ni corren la numeración.
MANIFIESTO = json.loads(
    idiomas.ruta(REND / "spreads-activos.json", IDIOMA).read_text(encoding="utf-8"))
# Cada hoja declara cuántas páginas ocupa. Antes se daba por hecho que eran
# dos —`paginas[i*2]`— y con el arquetipo «hoja» eso revienta con IndexError.
# El manifiesto lo trae desde `build_menu.py`; si falta, son 2 (el pliego de
# siempre), que es lo que hace que esto no rompa nada existente.
SPREADS, _p = [], 0
for _i, _s in enumerate(MANIFIESTO):
    _n = _s.get("paginas", 2)
    SPREADS.append((_p, _n,
                    f"menu-doble-pagina-{_i + 1}-{_s['slug']}"
                    f"{idiomas.sufijo(IDIOMA)}.png"))
    _p += _n


async def main():
    OUT.mkdir(exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 2000, "height": 1400},
                              device_scale_factor=2)
        await pg.goto(SRC.as_uri())
        # las fotos son pesadas: esperar a que todas estén decodificadas
        await pg.wait_for_function(
            "() => [...document.images].every(i => i.complete)", timeout=60000)
        await pg.wait_for_timeout(1500)
        paginas = await pg.query_selector_all("section.page")
        for desde, cuantas, nombre in SPREADS:
            cajas = [await paginas[j].bounding_box()
                     for j in range(desde, desde + cuantas)]
            x0 = min(c["x"] for c in cajas)
            y0 = min(c["y"] for c in cajas)
            await pg.screenshot(
                path=str(OUT / nombre), full_page=True,
                clip={"x": x0, "y": y0,
                      "width": max(c["x"] + c["width"] for c in cajas) - x0,
                      "height": max(c["y"] + c["height"] for c in cajas) - y0})
            print("·", nombre)
        await b.close()

asyncio.run(main())
