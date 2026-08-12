#!/usr/bin/env python3
"""El archivo que se manda a la imprenta: CMYK, con sangrado y marcas de corte.

Toma `output/menu-completo-plano.pdf` —las 16 páginas ya aplanadas, sin
transparencia viva— y lo deja en el estado que pide un taller: **nada en RGB,
el sangrado declarado en las cajas del PDF y las marcas de corte dibujadas.**

Qué hace, y por qué cada cosa:

**1. Separa a CMYK aquí, no en el taller.** Si el archivo va en RGB, la
conversión la hace la imprenta y **decide ella** qué pasa con los colores que no
imprimen. Fondo (raster) y texto (vector) se convierten con el **mismo** perfil,
así que un naranja de foto y un naranja de titular siguen siendo el mismo
naranja. El perfil viaja dentro del PDF como *OutputIntent*: el taller no tiene
que adivinar en qué CMYK está el archivo.

**2. La gama NO se pre-comprime — medido, no supuesto.** Las tapas sí lo hacen
(`preparar_imprenta.py`): se baja la croma píxel a píxel antes de separar, para
que el recorte no aplaste los degradados. Aquí se probaron las dos y **gana la
conversión directa**, en las tres cifras que se midieron sobre las páginas más
saturadas (portada, Compartir, De la Calle):

| | error medio contra el original | saturación impresa | detalle en zona fuera de gama |
|---|---|---|---|
| directo     | **7.6 – 9.2** | **0.531 – 0.573** | −4 % |
| comprimido  | 9.6 – 11.9 | 0.499 – 0.547 | −2 % |

Comprimir gana un 2 % de detalle y cuesta un **14 % de saturación** en la hoja
Infantil: la ilustración pierde el brillo del cielo y los edificios se
enturbian. Y §6.6 es explícita —la saturación no puede bajar—. Queda como
opción (`--comprimir-gama`), no como norma.

**3. El negro de texto va a una sola tinta.** El perfil convierte el negro puro
en un negro compuesto de **295 % de tinta y cuatro planchas**. En un cuerpo de
7 pt —que es casi todo este menú— eso enseña el desregistro de la máquina como
un halo de color alrededor de cada letra. Los negros y **grises casi neutros**
del texto vectorial se fuerzan a **K sola**, con la K buscada por luminancia,
no por regla de tres. Esto incluye `--texto-cuerpo`, que Chromium entrega ya
compuesto contra el fondo (#544D4A sobre pastel, #5A5350 sobre crema): es el
texto más pequeño y más repetido del menú, y salía a cuatro tintas. Las fotos
no se tocan: ahí el negro compuesto es lo correcto y da más profundidad.

**4. Sangrado y marcas.** La página crece a 212 × 305 mm para dejar sitio a las
marcas, y el PDF declara sus tres cajas: `MediaBox` (todo), `BleedBox` (los
192 × 285 con sangrado) y `TrimBox` (los 186 × 279 del corte final). Las marcas
se dibujan **fuera del sangrado**, en K sola.

**⚠️ El JPEG CMYK va SIN la marca Adobe y SIN `/Decode`.** Es la única
combinación que no depende de a quién le preguntes, y llegar a ella costó una
tirada.

El JPEG CMYK admite dos convenciones para los mismos bytes —muestras derechas
o invertidas— y la marca Adobe (APP14) es la que dice cuál. El problema es que
**los lectores no se ponen de acuerdo en si esa marca les incumbe**: medido
sobre un crema de 68 % de tinta total, con las muestras invertidas que escribe
PIL por omisión:

| | MuPDF / Quartz | Illustrator / Acrobat |
|---|---|---|
| APP14 + `/Decode [1 0 1 0 1 0 1 0]` | ✅ crema | 🔴 **negro** |
| APP14, sin `Decode` | 🔴 negro | ✅ crema |
| **sin APP14, sin `Decode`, muestras derechas** | ✅ crema | ✅ crema |

MuPDF **ignora** la marca y aplica solo el `Decode`; Illustrator aplica **las
dos**, invierte dos veces y un fondo de poca tinta se convierte en cuatro
planchas al tope: negro. Con la marca puesta, los dos motores no pueden acertar
a la vez — no hay combinación que los contente.

Por eso se le quita. Sin marca no hay nada que interpretar: cuatro canales,
`/ColorSpace /DeviceCMYK`, muestras derechas, uno a uno. Y como PIL invierte
siempre al guardar (rawmode `CMYK;I`), se le entrega la imagen ya invertida
para que su propia inversión la deje derecha.

📌 **Y por eso la prueba local no es prueba de esto.** `prueba-imprenta.jpg`
la pinta MuPDF, que era justo el motor que daba el visto bueno al archivo roto.
Lo que decide es abrirlo en Illustrator.

Salidas en `output/imprenta/`:
  · menu-parceros-CMYK-sangrado.pdf — **el archivo que se manda**
  · prueba-imprenta.jpg             — las 16 páginas juntas, para revisar antes de mandar

**5. Los dos idiomas salen del mismo proceso.** `--idioma en` cambia el archivo
de entrada y el nombre de salida, y **nada más**: mismo perfil, mismo límite de
tinta, mismo negro a una tinta, mismas cajas. Es lo que hace que las dos
versiones se puedan tirar en la misma máquina sin recalibrar — y el motivo por
el que esto es un flag y no un script aparte, que se habría desincronizado en la
primera corrección de color.

Uso:  python3 render/preparar_pdf_imprenta.py
      python3 render/preparar_pdf_imprenta.py --idioma en
      python3 render/preparar_pdf_imprenta.py --sin-marcas   # solo sangrado
"""
from __future__ import annotations

import argparse
import io
import re
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageChops, ImageCms

from . import variantes as idiomas
from . import preparar_imprenta as sep

from .preparar_imprenta import TOL, comprimir_gama, escala_croma, perfiles

# La raíz es la del CLIENTE, no la del paquete: aquí están su HTML, su
# CSS y sus datos. Deducirla de `__file__` daba site-packages.
from .proyecto import RAIZ as REND
from .proyecto import SALIDA as OUT
# El aplanado SIN los marcadores `.pendiente` (§1.3). El otro
# —`menu-completo-plano.pdf`— sí los lleva: es el de revisión.
ENTRADA = OUT / "menu-completo-plano-imprenta.pdf"
DESTINO = OUT / "imprenta"

MM = 72 / 25.4
# El corte, el sangrado y las marcas llegan de `formato.py` — fuente única.
# Aquí estaban tecleados, y un desacuerdo entre este archivo y `style.css` no
# da error: da un PDF cuyo TrimBox no cuadra con lo que dibujó Chromium, y eso
# solo se ve en la plancha.
from .formato import CORTE_MM, LARGO_MARCA_MM, MARCA_MM, SANGRADO_MM  # noqa: E402
from .formato import PAGINAS as PAGINAS_ESPERADAS  # noqa: E402

# 🏷️ El nombre del archivo lleva el del cliente, y el cliente lo dice la carta.
# Estaba escrito «menu-parceros-…»: montar la demo sacaba un archivo con el
# nombre de otro restaurante, que es el fallo que de verdad duele cuando hay
# dos PDF distintos esperando en la bandeja del taller.
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
GROSOR_MARCA = 0.25            # pt

CALIDAD = 92                   # JPEG del fondo; 4:4:4, sin submuestreo de croma
LIMITE_TINTA = 300             # % de cobertura total que admite un estucado
DPI_MINIMO = 300

# Cuándo un color de texto se manda a K sola (§3 del encabezado): tiene que ser
# casi neutro —los tres canales dentro de esta banda— y oscuro. El crema
# #F6EAE3 abre 0.075 y además es claro: se queda con su construcción cálida.
NEUTRO = 0.06
OSCURO = 0.55
LUMA = np.array([0.2126, 0.7152, 0.0722], np.float32)

SANGRADO_MM_TOT = (CORTE_MM[0] + 2 * SANGRADO_MM, CORTE_MM[1] + 2 * SANGRADO_MM)


# ─────────────────────────────────────────────────────────── perfil de salida

# Dónde se guardan los `.icc` del proyecto. El taller pidió **FOGRA39**
# (ISO 12647-2), que es también lo que manda `style-guide.md` §1 — pero ese
# perfil ya no se descarga de ninguna fuente confiable: ECI retiró sus
# descargas y Fogra vende la caracterización. Lo trae el taller, o cualquier
# instalación de Adobe: «Coated FOGRA39 (ISO 12647-2:2004).icc».
PERFILES = REND / "perfiles"


def resolver_perfil(pedido: str | None) -> str:
    """La ruta del `.icc` con el que se separa TODO: fondos, texto y etiqueta.

    Sin `--perfil`, se coge el único `.icc` de `render/perfiles/`. Si hay
    varios hay que nombrarlo: elegir por orden alfabético sería elegir a ciegas
    el espacio de color de una tirada entera.
    """
    if pedido:
        ruta = Path(pedido)
        if not ruta.exists():
            raise SystemExit(f"no existe el perfil {ruta}")
        return str(ruta)
    sueltos = sorted(PERFILES.glob("*.icc")) if PERFILES.is_dir() else []
    if len(sueltos) > 1:
        raise SystemExit(
            f"hay {len(sueltos)} perfiles en {PERFILES.name}/ — dime cuál con "
            "--perfil:\n" + "".join(f"  · {p.name}\n" for p in sueltos))
    return str(sueltos[0]) if sueltos else sep.CMYK


def nombre_perfil() -> str:
    """El nombre que el propio `.icc` declara, no el del archivo."""
    return ImageCms.getProfileDescription(
        ImageCms.getOpenProfile(sep.CMYK)).strip()


def texto_pdf(s: str) -> str:
    """Escapa una cadena literal de PDF: los paréntesis cierran el valor."""
    return s.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


# ─────────────────────────────────────────────────────────── color

def comprimir_color(rgb, fwd, bwd, iters=14):
    """`comprimir_gama()` para UN color plano.

    El texto vectorial tiene que recibir el mismo trato que el fondo: si el
    naranja de una foto se comprime y el del titular no, dejan de ser el mismo
    naranja en el papel.
    """
    base = np.array(rgb, np.float32).reshape(1, 1, 3)
    lo, hi = 0.0, 1.0
    for _ in range(iters):
        mid = (lo + hi) / 2
        cand = (np.clip(escala_croma(base, mid), 0, 1) * 255 + .5).astype(np.uint8)
        ida = ImageCms.applyTransform(ImageCms.applyTransform(
            Image.fromarray(cand), fwd), bwd)
        desvio = np.abs(np.asarray(ida).astype(np.float32) -
                        cand.astype(np.float32)).max()
        lo, hi = (mid, hi) if desvio <= TOL else (lo, mid)
    return np.clip(escala_croma(base, lo if hi < 1.0 else 1.0), 0, 1)


def k_por_luminancia(rgb, bwd, iters=14):
    """La K que imprime con la misma claridad que este gris.

    Buscada, no calculada: `1 − media` daría un gris más claro de lo debido,
    porque la K del perfil no es lineal y el negro máximo del papel no es 0.
    """
    objetivo = float(np.array(rgb, np.float32) @ LUMA)
    lo, hi = 0.0, 1.0
    for _ in range(iters):
        mid = (lo + hi) / 2
        px = np.array([[[0, 0, 0, round(mid * 255)]]], np.uint8)
        rgb_k = np.asarray(ImageCms.applyTransform(
            Image.fromarray(px, "CMYK"), bwd)).astype(np.float32)[0, 0] / 255
        lo, hi = (lo, mid) if float(rgb_k @ LUMA) < objetivo else (mid, hi)
    return round((lo + hi) / 2, 4)


def cmyk_de_rgb(rgb, fwd, bwd, comprimir=False):
    """Un color de texto, ya en CMYK. Los grises casi neutros, a K sola (§3)."""
    if max(rgb) - min(rgb) <= NEUTRO and sum(rgb) / 3 <= OSCURO:
        return (0.0, 0.0, 0.0, k_por_luminancia(rgb, bwd))
    plano = comprimir_color(rgb, fwd, bwd) if comprimir else \
        np.array(rgb, np.float32).reshape(1, 1, 3)
    px = (plano * 255 + .5).astype(np.uint8)
    tinta = np.asarray(ImageCms.applyTransform(Image.fromarray(px), fwd))[0, 0]
    return tuple(round(float(v) / 255, 4) for v in tinta)


def fuera_de_gama(im, fwd, bwd):
    chico = im.copy(); chico.thumbnail((900, 900))
    a = np.asarray(chico)
    ida = ImageCms.applyTransform(ImageCms.applyTransform(Image.fromarray(a), fwd), bwd)
    err = np.abs(np.asarray(ida).astype(np.float32) - a.astype(np.float32)).max(2)
    return float((err > TOL).mean() * 100)


def cobertura(cmyk):
    """Cobertura total de tinta: máximo y qué parte pasa del límite.

    ⚠️ A tamaño completo y en entero. Medirla sobre una miniatura da cifras que
    no existen: el remuestreo Lanczos sobrepasa en los bordes duros y hace
    aparecer un 314 % donde el archivo no pasa de 300.
    """
    tac = np.asarray(cmyk).astype(np.uint16).sum(2) / 255 * 100
    return float(tac.max()), float((tac > LIMITE_TINTA).mean() * 100)


def limitar_tinta(cmyk, limite=LIMITE_TINTA):
    """Baja el CMY —nunca la K— donde la cobertura total pasa del límite.

    Son las sombras más profundas de las fotos: un 0.1 % de la página, invisible
    a la vista. Pero por encima de 300 % la tinta no seca a tiempo, se repinta
    en la pila y el pliego sale con la imagen de la página de al lado.
    """
    a = np.asarray(cmyk).astype(np.float32)
    techo = limite / 100 * 255
    exceso = a.sum(2) > techo
    if not exceso.any():
        return cmyk, 0.0
    cmy, k = a[..., :3], a[..., 3]
    factor = np.where(exceso,
                      np.clip((techo - k) / np.maximum(cmy.sum(2), 1e-6), 0, 1), 1.0)
    a[..., :3] = cmy * factor[..., None]
    return (Image.fromarray(np.clip(a + .5, 0, 255).astype(np.uint8), "CMYK"),
            float(exceso.mean() * 100))


# ─────────────────────────────────────────────────────────── fondos

def jpeg_cmyk_sin_marca(cmyk, calidad):
    """JPEG CMYK con las muestras derechas y sin la marca Adobe (§ del encabezado).

    Dos vueltas de tuerca, las dos necesarias:

    · **Se invierte antes de guardar** porque PIL guarda el CMYK con rawmode
      `CMYK;I` —siempre invertido, no es opcional—. Entregarle la imagen ya
      invertida hace que su inversión la deje derecha.
    · **Se borra el segmento APP14** de los bytes ya escritos. PIL lo emite sin
      preguntar y no hay parámetro para evitarlo, así que se recorta el
      segmento entero: marcador (2 bytes) más su longitud declarada.
    """
    buf = io.BytesIO()
    ImageChops.invert(cmyk).save(buf, "JPEG", quality=calidad,
                                 subsampling=0, optimize=True)
    datos = bytearray(buf.getvalue())
    i = datos.find(b"\xff\xee")
    if i < 0:
        raise SystemExit(
            "el JPEG salió sin marca Adobe: PIL cambió de comportamiento y "
            "seguramente ya no invierte al guardar. Vuelve a medir las cuatro "
            "combinaciones antes de mandar nada a la plancha.")
    del datos[i:i + 2 + ((datos[i + 2] << 8) | datos[i + 3])]
    return bytes(datos)


def convertir_fondos(doc, calidad, comprimir=False, verbose=True):
    """Cada página lleva UN JPEG a página completa: se separa entero."""
    fwd, bwd = perfiles()
    hechos, informe = set(), []
    for i, pagina in enumerate(doc):
        imgs = pagina.get_images(full=True)
        if len(imgs) != 1:
            raise SystemExit(
                f"pág {i + 1}: se esperaba 1 imagen de fondo y hay {len(imgs)}. "
                "La entrada no es el aplanado de `build_pdf_plano.py`.")
        xref = imgs[0][0]
        if xref in hechos:
            continue

        im = Image.open(io.BytesIO(doc.xref_stream_raw(xref))).convert("RGB")
        antes = fuera_de_gama(im, fwd, bwd)
        origen, tocado = comprimir_gama(im) if comprimir else (im, 0.0)
        despues = fuera_de_gama(origen, fwd, bwd) if comprimir else antes

        cmyk = ImageCms.applyTransform(origen, fwd)
        antes_tinta, _ = cobertura(cmyk)
        cmyk, recortado = limitar_tinta(cmyk)
        tinta_max, sobre = cobertura(cmyk)
        datos = jpeg_cmyk_sin_marca(cmyk, calidad)

        doc.update_stream(xref, datos, compress=False)
        doc.xref_set_key(xref, "Filter", "/DCTDecode")
        doc.xref_set_key(xref, "ColorSpace", "/DeviceCMYK")
        doc.xref_set_key(xref, "Decode", "null")
        hechos.add(xref)

        dpi = im.width / (SANGRADO_MM_TOT[0] / 25.4)
        informe.append(dict(pagina=i + 1, dpi=dpi, antes=antes, despues=despues,
                            tocado=tocado, tinta=tinta_max, sobre=sobre,
                            recortado=recortado, mb=len(datos) / 1e6))
        if verbose:
            gama = (f"fuera de gama {antes:5.1f}% → {despues:4.1f}% "
                    f"(croma tocada en {tocado:4.1f}%)" if comprimir
                    else f"fuera de gama {antes:5.1f}%")
            tinta = (f"tinta {antes_tinta:3.0f}% → {tinta_max:3.0f}% "
                     f"(acotada en {recortado:.2f}% de la página)" if recortado
                     else f"tinta máx {tinta_max:3.0f}%")
            print(f"  pág {i + 1:2}  {dpi:.0f} dpi · {gama} · {tinta} · "
                  f"{len(datos) / 1e6:5.1f} MB")
    return informe


# ─────────────────────────────────────────────────────────── texto vectorial

RE_COLOR = re.compile(rb"(?<![\w.])(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(rg|RG)(?![\w])")
RE_GRIS = re.compile(rb"(?<![\w.])(-?[\d.]+)\s+(g|G)(?![\w])")


def flujos_de_contenido(doc):
    """Los xref que llevan operadores de pintura: `/Contents` y Form XObject.

    Se listan explícitamente en vez de barrer todos los flujos del documento:
    un barrido ciego acaba metiendo la expresión regular dentro de un perfil
    ICC o de un JPEG, donde tres números seguidos de `rg` son una casualidad.
    """
    xrefs = set()
    for pagina in doc:
        xrefs.update(pagina.get_contents())
        for x, *_ in pagina.get_xobjects():
            if doc.xref_get_key(x, "Subtype")[1] == "/Form":
                xrefs.add(x)
    return sorted(xrefs)


def convertir_texto(doc, comprimir=False, verbose=True):
    """Reescribe a CMYK los operadores de color RGB del contenido vectorial.

    Las Type3 de este PDF usan `d1` (solo silueta), así que heredan el color de
    fuera y no hay que tocarlas.
    """
    fwd, bwd = perfiles()
    cache, cambios, flujos = {}, 0, 0

    def sub_color(m):
        rgb = tuple(round(float(m.group(i)), 6) for i in (1, 2, 3))
        if rgb not in cache:
            cache[rgb] = cmyk_de_rgb(rgb, fwd, bwd, comprimir)
        c, mag, y, k = cache[rgb]
        return (f"{c:g} {mag:g} {y:g} {k:g} ".encode()
                + (b"k" if m.group(4) == b"rg" else b"K"))

    def sub_gris(m):
        # Un operador `g` ya es neutro por definición: va a K sola sin más
        # condiciones, aunque sea un gris claro.
        rgb = (round(float(m.group(1)), 6),) * 3
        if rgb not in cache:
            cache[rgb] = (0.0, 0.0, 0.0, k_por_luminancia(rgb, bwd))
        return (f"0 0 0 {cache[rgb][3]:g} ".encode()
                + (b"k" if m.group(2) == b"g" else b"K"))

    for x in flujos_de_contenido(doc):
        datos = doc.xref_stream(x)
        nuevo, n1, n2 = b"", 0, 0
        for trozo, es_cadena in tramos(datos):
            if es_cadena:
                # Dentro de `(...)` no se toca NADA: ahí `0 0 0 rg` es texto
                # que se imprime, no un operador de color.
                nuevo += trozo
                continue
            t, a = RE_COLOR.subn(sub_color, trozo)
            t, b = RE_GRIS.subn(sub_gris, t)
            nuevo, n1, n2 = nuevo + t, n1 + a, n2 + b
        if n1 + n2:
            doc.update_stream(x, nuevo)
            cambios += n1 + n2
            flujos += 1

    if verbose:
        print(f"  · {cambios} operadores reescritos en {flujos} flujos de contenido")
        for rgb, v in sorted(cache.items()):
            hexa = "#" + "".join(f"{round(c * 255):02X}" for c in rgb)
            sola = "   ← una sola tinta" if v[:3] == (0.0, 0.0, 0.0) else ""
            print(f"     {hexa}  →  C{v[0] * 100:3.0f} M{v[1] * 100:3.0f} "
                  f"Y{v[2] * 100:3.0f} K{v[3] * 100:3.0f}{sola}")
    return cambios


# ─────────────────────────────────────────────────────────── cajas y marcas

def tramos(datos):
    """Parte un flujo de contenido en `(trozo, es_cadena_literal)`.

    ⚠️ Existe porque la sustitución de color es una expresión regular, y una
    expresión regular no sabe distinguir un operador de un texto que se
    imprime: dentro de `(0 0 0 rg)` eso son cinco caracteres de tipografía,
    no una orden de tinta. Reescribirlos cambia lo que dice la carta.

    Antes había una guarda que se plantaba si el flujo llevaba un `(` —
    «este PDF no lleva ninguna»—. Y era cierto para un cliente: sus fuentes
    se incrustan como subconjunto y Chromium escribe el texto en hexadecimal,
    `<0043>`. Con otras fuentes lo escribe como cadena literal, y entonces el
    archivo de imprenta **no se podía generar**. El primer cliente que lo
    encontró fue el restaurante de ejemplo de este repo.

    Se recorre el flujo respetando el escape `\(` y el anidamiento de
    paréntesis, que es lo que dice la especificación de PDF para una cadena
    literal. Lo de fuera se sustituye; lo de dentro se copia tal cual.
    """
    out, i, n, ini = [], 0, len(datos), 0
    while i < n:
        c = datos[i]
        if c == 0x5C:            # \  — escape: se salta el siguiente byte
            i += 2
            continue
        if c == 0x28:            # (  — abre cadena literal
            if i > ini:
                out.append((datos[ini:i], False))
            prof, j = 1, i + 1
            while j < n and prof:
                if datos[j] == 0x5C:
                    j += 2
                    continue
                if datos[j] == 0x28:
                    prof += 1
                elif datos[j] == 0x29:
                    prof -= 1
                j += 1
            out.append((datos[i:j], True))
            i = ini = j
            continue
        i += 1
    if ini < n:
        out.append((datos[ini:], False))
    return out


def dims_media(marcas=True):
    m = MARCA_MM if marcas else 0.0
    return (SANGRADO_MM_TOT[0] + 2 * m, SANGRADO_MM_TOT[1] + 2 * m)


def cajas_y_marcas(doc, marcas=True):
    """Agranda la página, declara las tres cajas y dibuja las marcas de corte.

    ⚠️ Las cajas del PDF viven en el sistema de coordenadas del CONTENIDO, cuyo
    origen sigue en la esquina de la página con sangrado: al agrandar la
    `MediaBox` hacia fuera, su origen se vuelve negativo y las otras dos cajas
    NO se mueven. El dibujo de las marcas, en cambio, usa las coordenadas de
    fitz —origen arriba-izquierda de la página ya agrandada—.
    """
    m = (MARCA_MM if marcas else 0.0) * MM
    wb, hb = (v * MM for v in SANGRADO_MM_TOT)
    s = SANGRADO_MM * MM
    for pagina in doc:
        if m:
            r = pagina.mediabox
            pagina.set_mediabox(fitz.Rect(r.x0 - m, r.y0 - m, r.x1 + m, r.y1 + m))
        mb = pagina.mediabox
        doc.xref_set_key(pagina.xref, "CropBox",
                         f"[{mb.x0:g} {mb.y0:g} {mb.x1:g} {mb.y1:g}]")
        doc.xref_set_key(pagina.xref, "BleedBox", f"[0 0 {wb:g} {hb:g}]")
        doc.xref_set_key(pagina.xref, "TrimBox",
                         f"[{s:g} {s:g} {wb - s:g} {hb - s:g}]")

        if not marcas:
            continue
        x0, x1 = m + s, m + wb - s          # líneas de corte verticales
        y0, y1 = m + s, m + hb - s          # líneas de corte horizontales
        L = LARGO_MARCA_MM * MM
        seg = []
        for x in (x0, x1):
            seg += [((x, y0 - s), (x, y0 - s - L)), ((x, y1 + s), (x, y1 + s + L))]
        for y in (y0, y1):
            seg += [((x0 - s, y), (x0 - s - L, y)), ((x1 + s, y), (x1 + s + L, y))]
        forma = pagina.new_shape()
        for a, b in seg:
            forma.draw_line(fitz.Point(*a), fitz.Point(*b))
        forma.finish(color=(0, 0, 0, 1), width=GROSOR_MARCA)   # K sola
        forma.commit()


def intento_de_salida(doc):
    """Mete el perfil CMYK dentro del PDF como OutputIntent.

    ⚠️ Lee `sep.CMYK`, que es **el mismo** con el que se separó todo unas
    líneas más arriba. Declarar aquí un perfil distinto del que se usó es peor
    que no declarar ninguno: el taller confía en la etiqueta y vuelve a
    convertir desde un espacio que el archivo nunca tuvo.
    """
    x_icc = doc.get_new_xref()
    doc.update_object(x_icc, "<< /N 4 >>")
    doc.update_stream(x_icc, Path(sep.CMYK).read_bytes(), compress=True)
    x_oi = doc.get_new_xref()
    doc.update_object(x_oi, (
        "<< /Type /OutputIntent /S /GTS_PDFX "
        f"/OutputConditionIdentifier ({texto_pdf(nombre_perfil())}) "
        f"/OutputCondition (Separacion CMYK, {LIMITE_TINTA}% de tinta) "
        f"/Info ({texto_pdf(Path(sep.CMYK).name)}) "
        f"/DestOutputProfile {x_icc} 0 R >>"))
    doc.xref_set_key(doc.pdf_catalog(), "OutputIntents", f"[ {x_oi} 0 R ]")


# ─────────────────────────────────────────────────────────── verificación

def _geometria(doc, fallos, avisos):
    """Las tres cosas que solo se ven cuando entra la guillotina.

    ⚠️ Nacen de probar un formato NUEVO. Las cajas ya se comprobaban —miden lo
    que dice el formato— pero eso no dice nada sobre lo que pasa al cortar:
    una caja correcta con el fondo a medio llegar deja una tira blanca en el
    borde, y un texto a 1 mm del corte se decapita con la tolerancia normal de
    una guillotina.

    Son baratas y solo importan de verdad la primera vez que se imprime un
    formato. Por eso van aquí y no en una herramienta aparte que nadie corre.
    """
    import re as _re
    for i, pg in enumerate(doc):
        crudo = doc.xref_object(pg.xref)

        def caja(n):
            m = _re.search(rf"/{n}\s*\[([^\]]+)\]", crudo)
            return [float(x) / MM for x in m.group(1).split()] if m else None

        M, B, T = caja("MediaBox"), caja("BleedBox"), caja("TrimBox")
        if not (M and B and T):
            continue

        # 1 · cada caja centrada dentro de la anterior
        for a, b, et, esp in ((M, B, "marcas", MARCA_MM), (B, T, "sangrado", SANGRADO_MM)):
            lados = [b[0] - a[0], a[2] - b[2], b[1] - a[1], a[3] - b[3]]
            if any(abs(x - esp) > 0.1 for x in lados):
                fallos.append(f"pág {i+1}: el {et} no está centrado "
                              f"({' · '.join(f'{x:.2f}' for x in lados)} mm, "
                              f"esperado {esp})")

        # 2 · nada vivo demasiado cerca del corte
        #
        # ⚠️ El TrimBox se recalcula en ESPACIO DE PÁGINA. `pg.trimbox` de
        # PyMuPDF mezcla espacios —devuelve la x en crudo y la y ya
        # trasladada—, y los bbox de `get_text` vienen en espacio de página
        # (origen en la esquina superior izquierda del MediaBox). Compararlos
        # directamente resta de menos exactamente `MARCA_MM`.
        #
        # No es teórico: la primera versión de esta comprobación denunció
        # texto «a 3.2 mm del corte» en un menú que lo tiene a 13.2. Diez
        # milímetros de diferencia, que es justo el margen de marcas.
        tb = fitz.Rect(T[0] - M[0], M[3] - T[3], T[2] - M[0], M[3] - T[1]) * MM
        cerca, quien = 99.0, ""
        for blq in pg.get_text("dict")["blocks"]:
            for ln in blq.get("lines", []):
                for s in ln["spans"]:
                    x0, y0, x1, y1 = s["bbox"]
                    dd = min(x0 - tb.x0, tb.x1 - x1, y0 - tb.y0, tb.y1 - y1) / MM
                    if dd < cerca:
                        cerca, quien = dd, s["text"][:30]
        if cerca < 2:
            fallos.append(f"pág {i+1}: texto a {cerca:.1f} mm del corte «{quien}»")
        elif cerca < 4:
            avisos.append(f"pág {i+1}: solo {cerca:.1f} mm hasta el corte «{quien}» "
                          f"— la guillotina se mueve más que eso")

    # 3 · las marcas, en K sola
    tinta = set()
    for pg in doc:
        flujo = b"".join(doc.xref_stream(x) for x in pg.get_contents())
        tinta |= set(_re.findall(rb"([\d.]+ [\d.]+ [\d.]+ [\d.]+)\s+K\b", flujo))
    if tinta and not all(k.split()[:3] == [b"0", b"0", b"0"] for k in tinta):
        fallos.append("las marcas de corte no van en K sola — se verá el "
                      "desregistro de la máquina en la propia marca")


def verificar(ruta: Path, marcas=True):
    doc = fitz.open(ruta)
    fallos = []
    esperada = tuple(round(v, 1) for v in dims_media(marcas))
    corte = tuple(round(v, 1) for v in CORTE_MM)
    sangre = tuple(round(v, 1) for v in SANGRADO_MM_TOT)

    avisos = []
    if doc.page_count != PAGINAS_ESPERADAS:
        fallos.append(f"{doc.page_count} páginas, no {PAGINAS_ESPERADAS}")
    _geometria(doc, fallos, avisos)
    for a in avisos:
        print(f"  🟡 {a}")

    def mm(caja):
        return (round(caja.width / MM, 1), round(caja.height / MM, 1))

    for i, pagina in enumerate(doc):
        n = i + 1
        if mm(pagina.mediabox) != esperada:
            fallos.append(f"pág {n}: MediaBox {mm(pagina.mediabox)} ≠ {esperada} mm")
        if mm(pagina.trimbox) != corte:
            fallos.append(f"pág {n}: TrimBox {mm(pagina.trimbox)} ≠ {corte} mm")
        if mm(pagina.bleedbox) != sangre:
            fallos.append(f"pág {n}: BleedBox {mm(pagina.bleedbox)} ≠ {sangre} mm")
        for img in pagina.get_images(full=True):
            if img[5] != "DeviceCMYK":
                fallos.append(f"pág {n}: imagen en {img[5]}, no DeviceCMYK")
            dpi = img[2] / (SANGRADO_MM_TOT[0] / 25.4)
            if dpi < DPI_MINIMO:
                fallos.append(f"pág {n}: fondo a {dpi:.0f} dpi (mínimo {DPI_MINIMO})")
            # Las dos formas de que las fotos salgan invertidas —negras— en
            # Illustrator. Se comprueban aquí porque la hoja de prueba la pinta
            # MuPDF, que ignora la marca Adobe y da el visto bueno igual.
            if doc.xref_get_key(img[0], "Decode")[0] != "null":
                fallos.append(f"pág {n}: la imagen lleva /Decode")
            if b"\xff\xee" in doc.xref_stream_raw(img[0])[:4096]:
                fallos.append(f"pág {n}: el JPEG lleva la marca Adobe (APP14)")
        for f in pagina.get_fonts(full=True):
            if f[2] == "Type3":          # sus glifos van dentro del propio PDF
                continue
            if not doc.extract_font(f[0])[3]:
                fallos.append(f"pág {n}: fuente {f[3]} sin incrustar")

    rgb = sum(len(RE_COLOR.findall(d)) + len(RE_GRIS.findall(d))
              for d in (doc.xref_stream(x) for x in flujos_de_contenido(doc)))
    if rgb:
        fallos.append(f"{rgb} operadores de color RGB/gris sin convertir")

    trans = sum(1 for x in range(1, doc.xref_length())
                if "/Luminosity" in (doc.xref_object(x) or ""))
    if trans:
        fallos.append(f"{trans} máscaras suaves de luminosidad (transparencia viva)")
    if not doc.xref_get_key(doc.pdf_catalog(), "OutputIntents")[1]:
        fallos.append("sin OutputIntent")
    doc.close()
    return fallos


def hoja_de_prueba(ruta: Path, salida: Path, dpi=36):
    """Las 16 páginas en una sola imagen, para mirarlas antes de mandar nada."""
    doc = fitz.open(ruta)
    minis = []
    for p in doc:
        px = p.get_pixmap(dpi=dpi)
        minis.append(Image.frombytes("RGB", (px.width, px.height), px.samples))
    doc.close()
    w, h = minis[0].size
    cols, filas, hueco = 8, 2, 8
    hoja = Image.new("RGB", (cols * w + (cols + 1) * hueco,
                             filas * h + (filas + 1) * hueco), (235, 235, 235))
    for i, m in enumerate(minis):
        hoja.paste(m, (hueco + (i % cols) * (w + hueco),
                       hueco + (i // cols) * (h + hueco)))
    hoja.save(salida, "JPEG", quality=88)
    return hoja.size


# ─────────────────────────────────────────────────────────── main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrada", default=None,
                    help="por omisión, el aplanado de imprenta del idioma pedido")
    ap.add_argument("--idioma", default="es", choices=idiomas.DISPONIBLES)
    ap.add_argument("--perfil", default=None,
                    help="el .icc de salida; por omisión, el de render/perfiles/")
    ap.add_argument("--calidad", type=int, default=CALIDAD)
    ap.add_argument("--sin-marcas", action="store_true",
                    help="sangrado y cajas, pero sin marcas de corte")
    ap.add_argument("--comprimir-gama", action="store_true",
                    help="baja la croma antes de separar (§2: mide antes de usarlo)")
    args = ap.parse_args()
    marcas = not args.sin_marcas

    # ⚠️ Antes de separar nada: `perfiles()` lee este global cada vez que se
    # llama, así que fijarlo aquí alcanza para fondos, texto y OutputIntent.
    sep.CMYK = resolver_perfil(args.perfil)

    suf = idiomas.sufijo(args.idioma)
    entrada = (Path(args.entrada) if args.entrada
               else idiomas.ruta(ENTRADA, args.idioma))
    if not entrada.exists():
        raise SystemExit(
            f"falta {entrada}. Corre antes:\n"
            f"  python3 render/build_tapas_final.py --idioma {args.idioma} && "
            f"python3 render/build_pdf_plano.py --imprenta --idioma {args.idioma}")
    DESTINO.mkdir(parents=True, exist_ok=True)
    # ⚠️ El nombre lleva el idioma SIEMPRE que no sea español, y no es cosmético:
    # los dos archivos van al mismo taller y se diferencian solo por el texto de
    # dentro. Sin sufijo, el segundo pisa al primero y nadie se entera hasta que
    # llegan 2 000 ejemplares del mismo idioma.
    salida = DESTINO / f"menu-{CLIENTE}-CMYK-sangrado{suf}.pdf"

    doc = fitz.open(entrada)
    print(f"entrada: {entrada.name} · {doc.page_count} páginas · "
          f"idioma {args.idioma}")
    print(f"perfil:  {nombre_perfil()}  ({Path(sep.CMYK).name})")
    if not Path(sep.CMYK).is_relative_to(PERFILES):
        print("  🟡 perfil de sistema, no uno de imprenta. El taller pidió "
              "FOGRA39:\n     pídele su .icc, déjalo en "
              f"{PERFILES.relative_to(REND.parent)}/ y vuelve a correr esto.")
    print()
    print("Fondos — separación a CMYK"
          + (" con compresión de gama:" if args.comprimir_gama else " directa:"))
    informe = convertir_fondos(doc, args.calidad, args.comprimir_gama)
    print("\nTexto vectorial:")
    convertir_texto(doc, args.comprimir_gama)
    print("\nCajas y marcas:")
    cajas_y_marcas(doc, marcas)
    W, H = dims_media(marcas)
    print(f"  · MediaBox {W:g} × {H:g} mm · "
          f"BleedBox {SANGRADO_MM_TOT[0]:g} × {SANGRADO_MM_TOT[1]:g} mm · "
          f"TrimBox {CORTE_MM[0]:g} × {CORTE_MM[1]:g} mm"
          + ("" if marcas else "   (sin marcas)"))
    intento_de_salida(doc)
    doc.save(salida, deflate=True, garbage=4)
    doc.close()

    prueba = DESTINO / f"prueba-imprenta{suf}.jpg"
    hoja_de_prueba(salida, prueba)

    print(f"\n  → {salida.relative_to(REND.parent)}  ·  "
          f"{salida.stat().st_size / 1e6:.1f} MB")
    print(f"  → {prueba.relative_to(REND.parent)}  "
          f"({PAGINAS_ESPERADAS} páginas, para revisar)")

    fallos = verificar(salida, marcas)
    tinta = max(p["tinta"] for p in informe)
    sobre = max(p["sobre"] for p in informe)
    recortado = max(p["recortado"] for p in informe)
    if tinta > LIMITE_TINTA + 1:
        fallos.append(f"la cobertura de tinta llega a {tinta:.0f}%, por encima "
                      f"de {LIMITE_TINTA}%")
    print(f"\nCobertura de tinta: máx {tinta:.0f}% · acotada en hasta el "
          f"{recortado:.2f}% de una página · sobre {LIMITE_TINTA}%: {sobre:.2f}%")
    print("\nVerificación:")
    if fallos:
        for f in fallos:
            print(f"  🔴 {f}")
        raise SystemExit(1)
    print(f"  ✅ {PAGINAS_ESPERADAS} páginas · todo en CMYK · sangrado y cajas declarados · "
          "fuentes incrustadas · sin transparencia viva · OutputIntent incrustado")


if __name__ == "__main__":
    main()
