#!/usr/bin/env python3
"""¿El texto en inglés se sale de su caja? Lo mide, no lo estima.

Por qué hace falta
==================
`verificar_traduccion.py` comprueba que el ESQUELETO es idéntico: las mismas
cajas, en el mismo orden. Eso no dice nada del problema propio de traducir un
impreso: **el inglés y el español no ocupan lo mismo**. Una descripción que en
español entra en tres renglones puede pedir cuatro en inglés, y esa cuarta
línea no rompe el HTML — empuja lo de abajo, y lo de abajo puede ser el precio,
el pie, o el borde de la página.

Es exactamente la regla del proyecto medida en vez de supuesta: *«Medir, no
estimar. Ninguna unidad de espaciado se da por buena sin verla montada en el
render.»*

Qué mide
========
🔴 **Fuera de la página.** Contenido que rebasa la caja de la página. Es lo que
   se corta en la guillotina.
🔴 **Fuera de la caja de seguridad.** Texto a menos del margen mínimo del
   borde de corte. §6.56-ter documenta el caso: una ficha se fue a 2.9 mm.
🟡 **Creció respecto al español.** El bloque ocupa más alto que su gemelo. No
   es un fallo por sí solo —hay aire de sobra en varias hojas— pero es la
   lista de sitios donde mirar el PNG.

Uso
---
    python3 render/herramientas/medir_desborde.py
    python3 render/herramientas/medir_desborde.py --margen 4
"""
import argparse
import asyncio
import sys
from pathlib import Path

from playwright.async_api import async_playwright

REND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REND))

import idiomas  # noqa: E402

# Milímetros de seguridad desde el borde de CORTE. El menú lleva 3 mm de
# sangrado, así que la página renderizada mide 192 × 285 y el corte cae a 3 mm
# de cada lado.
SANGRADO_MM = 3
MARGEN_MM = 5
PX_MM = 96 / 25.4

# Lo que se mide: bloques de contenido con texto dentro. No se miden las fotos
# (su recorte lo audita `auditar_resolucion.py`) ni las capas decorativas.
SELECTOR = (".desc, .nombre-display, .hero-lista, .hero-punch, .item-nota, "
            ".adic-linea, .cruce-linea, .cruce-mesa, .bebida-item, .bg-fila, "
            ".cl-item, .cx-hero-cap, .cd-panel, .adic-fila, .patitos-txt, "
            ".hero-glosa, .hero-adiciones, .lista-sub, .cafe-cierre")

JS = """
(sel) => {
  const fuera = [];
  document.querySelectorAll('section.page').forEach((pg, ip) => {
    const p = pg.getBoundingClientRect();
    pg.querySelectorAll(sel).forEach(el => {
      const r = el.getBoundingClientRect();
      if (r.width === 0 && r.height === 0) return;
      fuera.push({
        pagina: ip,
        clase: el.className.toString().split(' ')[0],
        texto: (el.innerText || '').replace(/\\s+/g, ' ').trim().slice(0, 60),
        alto: r.height,
        sobra_der: r.right - p.right,
        sobra_izq: p.left - r.left,
        sobra_abajo: r.bottom - p.bottom,
        sobra_arriba: p.top - r.top,
      });
    });
  });
  return fuera;
}
"""


async def medir(pg, ruta):
    await pg.goto(ruta.as_uri())
    await pg.wait_for_function(
        "() => [...document.images].every(i => i.complete)", timeout=120000)
    await pg.evaluate("document.fonts.ready")
    await pg.wait_for_timeout(800)
    return await pg.evaluate(JS, SELECTOR)


async def main(margen_mm, codigo):
    seguro = (SANGRADO_MM - margen_mm) * PX_MM   # negativo = hacia dentro
    corte = SANGRADO_MM * PX_MM

    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 2000, "height": 1400})
        es = await medir(pg, REND / "menu-completo.html")
        en = await medir(pg, idiomas.ruta(REND / "menu-completo.html", codigo))
        await b.close()

    errores, avisos = [], []

    # Clave estable entre idiomas: página + clase + posición dentro de la
    # página. NO se usa el texto — es justo lo que cambia entre versiones.
    def indexar(items):
        out, cuenta = {}, {}
        for it in items:
            k = (it["pagina"], it["clase"])
            cuenta[k] = cuenta.get(k, 0) + 1
            out[(*k, cuenta[k])] = it
        return out

    ies, ien = indexar(es), indexar(en)

    for k, it in ien.items():
        pag = it["pagina"] + 1
        # 🔴 se sale de la página
        peor = max(it["sobra_der"], it["sobra_izq"],
                   it["sobra_abajo"], it["sobra_arriba"])
        if peor > 0.5:
            errores.append(
                f"p{pag} · {it['clase']}: se sale {peor / PX_MM:.1f} mm "
                f"de la página — «{it['texto']}»")
            continue
        # 🔴 entra en la caja de seguridad
        dentro = max(it["sobra_der"], it["sobra_izq"],
                     it["sobra_abajo"], it["sobra_arriba"])
        if dentro > seguro:
            mm = (corte - (-dentro)) / PX_MM
            errores.append(
                f"p{pag} · {it['clase']}: a {mm:.1f} mm del corte "
                f"(mínimo {margen_mm}) — «{it['texto']}»")
            continue
        # 🟡 creció respecto al español
        gemelo = ies.get(k)
        if gemelo and it["alto"] - gemelo["alto"] > 4:
            avisos.append(
                f"p{pag} · {it['clase']}: +{(it['alto'] - gemelo['alto']) / PX_MM:.1f} mm "
                f"más alto que en español — «{it['texto']}»")

    for a in avisos:
        print(f"🟡 {a}")
    for e in errores:
        print(f"🔴 {e}")

    print(f"\n{len(ien)} bloques medidos en «{codigo}» · {len(errores)} fuera "
          f"de caja · {len(avisos)} más altos que el español")
    if errores:
        raise SystemExit(1)
    print("✅ Nada se sale de la página ni entra en la caja de seguridad.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--margen", type=float, default=MARGEN_MM,
                    help="mm mínimos desde el borde de corte")
    ap.add_argument("--idioma", default="en")
    a = ap.parse_args()
    asyncio.run(main(a.margen, a.idioma))
