#!/usr/bin/env python3
"""Deja la portada lista para imprenta sin pasar por un ilustrador.

Dos problemas reales y qué se hace con cada uno:

**1. Color fuera de gama (el grave).** La escena es toda dorados y naranjas —
la familia que peor sobrevive a la tinta— y el 55 % de sus píxeles no
sobreviven un viaje a CMYK. Si se manda así, la imprenta hace la conversión
por su cuenta y **decide ella** qué hacer con esos colores: el resultado
típico es que los dorados se apagan y los naranjas se ensucian, todos de
golpe y sin control.
La solución es **comprimir la croma antes**, píxel a píxel y solo donde hace
falta: se busca por bisección cuánta saturación puede conservar cada zona sin
salirse. Los colores que ya imprimen no se tocan. Lo que se ve en pantalla
pasa a ser lo que sale en papel.

**2. Resolución.** El arte nace a 1024×1536 (135 dpi a tamaño de página) y se
amplía a 300. Eso **no inventa detalle**, pero aquí importa menos de lo que
parece: es una pintura de pincelada suave, no una fotografía con microdetalle.
No hay grano de sensor ni texturas finas que reconstruir. A distancia de
lectura no se ven píxeles; se ve un poco más blando de lo ideal. Es la
diferencia entre "correcto" y "excelente", no entre "imprimible" y "no".

Salidas en `output/imprenta/`:
  · portada-CMYK.tif   — la que se manda: CMYK, 300 dpi, con sangrado
  · portada-prueba.png — cómo se verá impresa (soft proof en pantalla)
  · portada-sRGB.png   — respaldo en RGB por si la imprenta prefiere convertir

Uso:  python3 render/preparar_imprenta.py
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageCms, ImageFilter

REND = Path(__file__).parent
OUT = REND.parent / "output" / "imprenta"
# Se puede pasar por argumento: portada, contraportada o el pliego entero.
PIEZAS = {
    "portada": "portada-final-300dpi.png",
    "contraportada": "contraportada-final-300dpi.png",
    "tapas": "tapas-imprenta-300dpi.png",
}

SRGB = "/System/Library/ColorSync/Profiles/sRGB Profile.icc"
CMYK = "/System/Library/ColorSync/Profiles/Generic CMYK Profile.icc"
LUMW = np.array([0.2126, 0.7152, 0.0722], np.float32)
TOL = 12.0                      # cuánto desvío se acepta como "imprime igual"


def perfiles():
    src, dst = ImageCms.getOpenProfile(SRGB), ImageCms.getOpenProfile(CMYK)
    return (ImageCms.buildTransform(src, dst, "RGB", "CMYK", renderingIntent=0),
            ImageCms.buildTransform(dst, src, "CMYK", "RGB", renderingIntent=0))


def error_gama(arr8, fwd, bwd):
    """Cuánto cambia cada píxel al ir a CMYK y volver."""
    ida = ImageCms.applyTransform(ImageCms.applyTransform(
        Image.fromarray(arr8), fwd), bwd)
    return np.abs(np.asarray(ida).astype(np.float32) - arr8.astype(np.float32)).max(2)


def escala_croma(rgb, f):
    """Acerca al gris conservando la luminancia: baja saturación, no brillo."""
    lum = (rgb @ LUMW)[..., None]
    return lum + (rgb - lum) * f


def comprimir_gama(im, iters=11, escala=3, margen=0.96):
    """Baja la croma SOLO de lo que no imprime, y lo justo.

    El mapa de factores se calcula en una versión reducida (es un mapa suave,
    no necesita resolución) y se aplica a tamaño completo. Así el cálculo pasa
    de minutos a segundos sin diferencia visible.
    """
    fwd, bwd = perfiles()
    chico = im.resize((im.width // escala, im.height // escala), Image.LANCZOS)
    base = np.asarray(chico).astype(np.float32) / 255

    lo = np.zeros(base.shape[:2], np.float32)
    hi = np.ones(base.shape[:2], np.float32)
    for _ in range(iters):
        mid = (lo + hi) / 2
        cand = (np.clip(escala_croma(base, mid[..., None]), 0, 1) * 255 + .5).astype(np.uint8)
        ok = error_gama(cand, fwd, bwd) <= TOL
        hi = np.where(ok, hi, mid)
        lo = np.where(ok, mid, lo)
    f = np.where(hi < 1.0, lo, 1.0)

    # margen: el desenfoque siguiente relaja el mapa, así que se compensa antes
    f = np.clip(f * margen, 0, 1)
    fmap = Image.fromarray((f * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.4))
    fmap = fmap.resize(im.size, Image.LANCZOS)
    f_full = np.asarray(fmap).astype(np.float32)[..., None] / 255

    full = np.asarray(im).astype(np.float32) / 255
    out = np.clip(escala_croma(full, f_full), 0, 1)
    return Image.fromarray((out * 255 + .5).astype(np.uint8)), (f < 0.999).mean() * 100


def resumen(im, fwd, bwd, etiqueta):
    chico = im.copy(); chico.thumbnail((1200, 1200))
    a = np.asarray(chico)
    err = error_gama(a, fwd, bwd)
    print(f"  {etiqueta:22} fuera de gama {(err > TOL).mean() * 100:5.1f}%  "
          f"desvío máx {err.max():3.0f}/255")


def main():
    import sys
    OUT.mkdir(parents=True, exist_ok=True)
    fwd, bwd = perfiles()
    pieza = sys.argv[1] if len(sys.argv) > 1 else "portada"
    ancho_mm = 384 if pieza == "tapas" else 192
    im = Image.open(REND.parent / "output" / PIEZAS[pieza]).convert("RGB")
    print(f"{pieza}: {im.size[0]}×{im.size[1]} px · "
          f"{im.size[0] / (ancho_mm / 25.4):.0f} dpi")

    resumen(im, fwd, bwd, "antes")
    corregida, pct = comprimir_gama(im)
    resumen(corregida, fwd, bwd, "después")
    print(f"  croma comprimida en el {pct:.1f}% de la imagen")

    corregida.save(OUT / f"{pieza}-sRGB.png", dpi=(300, 300))

    # El archivo que se manda: CMYK de verdad, no RGB con nombre bonito.
    cmyk = ImageCms.applyTransform(corregida, fwd)
    cmyk.save(OUT / f"{pieza}-CMYK.tif", dpi=(300, 300), compression="tiff_lzw")

    # Soft proof: cómo se verá en papel, para aprobar sin sorpresas.
    ImageCms.applyTransform(cmyk, bwd).save(OUT / f"{pieza}-prueba.png", dpi=(300, 300))

    for f in sorted(OUT.glob(f"{pieza}-*")):
        print(f"  · {f.name}  {f.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
