"""piezas — extraído de `build_menu.py`.

⚠️ El REPARTO de este archivo lo genera `herramientas/partir_build_menu.py`.
   Si algo está en el módulo equivocado, se ajusta el MANIFIESTO del
   splitter y se vuelve a correr — no se mueve a mano.
   El CONTENIDO (platillos, precios, textos) sí se edita aquí.
"""
from html import escape
import re

from .iconos import HOJA, ICO_PERSONAS
from .idioma import t, tn, tnx, ts, tx

# ---------- piezas de texto compartidas ----------

def nombre_html(it):
    # ⚠️ El nombre va por `tnx()`, la vía LENIENTE: por omisión se imprime en
    # español —«Patacones Recocheros» se lee igual en las dos versiones y es la
    # descripción la que explica qué es (dueño, 2026-08-02)— y solo se traduce
    # si el catálogo lo pide expresamente. Hoy lo pide uno: «Tiras de Pollo con
    # Papitas a la Francesa», que no es un nombre propio sino la lista de lo
    # que trae el plato. Ver `motor/idioma.py`.
    uni = f'<span class="nombre-unidades">{escape(it["u"])}</span>' if it.get("u") else ""
    # §6.57: el nombre puede partirse con "|" en dos líneas, la segunda en
    # naranja. Es el mismo mecanismo que ya tenían los HERO, traído al listado
    # para la hoja infantil: un nombre de dos colores se lee como logotipo de
    # personaje y no como entrada de catálogo. Fuera de esa hoja nadie lo usa.
    # Se traduce ANTES de partir por "|": el corte de dos líneas puede no caer
    # en la misma palabra en inglés.
    nombre = tn(it["n"])
    if "|" in nombre:
        a, b = nombre.split("|", 1)
        out = (f'<p class="nombre-display">{escape(a)}'
               f'<span class="nd-2">{escape(b)}</span>{uni}</p>')
        if it.get("n2"):
            out += f'<p class="nombre-script">{tnx(it["n2"])}</p>'
        return out
    out = f'<p class="nombre-display">{escape(nombre)}{uni}</p>'
    if it.get("n2"):
        out += f'<p class="nombre-script">{tnx(it["n2"])}</p>'
    return out

def personas_html(per):
    """Línea de personas (§6.17.6): icono + nº en oscuro; la nota
    ("pedir al centro") diferenciada en naranja tras un punto.
    (Los tags de decisión se probaron y quedaron descartados — §6.19.)"""
    partes = ts(per, "·")
    out = f'<p class="personas">{ICO_PERSONAS}<span>{escape(partes[0])}</span>'
    if len(partes) > 1:
        out += f'<span class="p-sep">•</span><span class="p-nota">{escape(partes[1])}</span>'
    return out + "</p>"

def precio_html(it):
    if it.get("precio"):
        return f'<span class="precio">{escape(it["precio"])}</span>'
    return '<span class="precio pend">precio pendiente</span>'

def cuerpo_html(it, con_precio=True):
    per = personas_html(it["per"]) if it.get("per") else ""
    if it.get("seg"):
        # §6.17.7: descripción escaneable — los mismos textos de
        # estructura-menu.md partidos en segmentos separados por •
        desc = f'<p class="desc">{" • ".join(tx(x) for x in it["seg"])}</p>'
    elif it.get("desc"):
        # los \n del texto aprobado se respetan como salto de línea;
        # la primera línea (gancho) va en seminegrilla (§6.17.7e)
        # Se traduce la descripción ENTERA y se parte después: el gancho y su
        # cuerpo se aprueban juntos y en inglés el corte puede no caer en la
        # misma frase (ver `ts` en `motor/idioma.py`).
        d = t(it["desc"])
        if "\n" in d:
            gancho, resto = d.split("\n", 1)
            cuerpo = (f'<span class="desc-gancho">{escape(gancho)}</span><br>'
                      f'{escape(resto).replace(chr(10), "<br>")}')
        else:
            cuerpo = escape(d)
        # [[hoja:palabra]] → la palabra y la ramita quedan pegadas y NUNCA se
        # separan por un salto de línea (§6.30-quater)
        cuerpo = re.sub(r"\[\[hoja:([^\]]+)\]\]",
                        lambda m: f'<span class="con-hoja">{m.group(1)}{HOJA}</span>',
                        cuerpo)
        desc = f'<p class="desc">{cuerpo}</p>'
    elif it.get("gancho"):
        # Gancho SIN cuerpo: para la fila que no necesita describirse (el
        # nombre ya dice qué es) pero que al lado de dos filas con gancho +
        # cuerpo se leía como inacabada. Sin esto habría que meterlo en "desc"
        # con un \n final, que deja un <br> huérfano.
        desc = f'<p class="desc"><span class="desc-gancho">{tx(it["gancho"])}</span></p>'
    elif it.get("sin_desc"):
        # DECIDIDO que no lleva descripción, no pendiente de escribirla: el
        # nombre ya dice qué es (Tiras de Pollo con Papitas, 2026-07-27).
        # Sin esta rama, un platillo cerrado se imprimiría con el marcador
        # punteado de "descripción pendiente" y parecería un olvido.
        desc = ""
    else:
        desc = '<p class="desc"><span class="pend-desc">descripción pendiente</span></p>'
    # Nota discreta del listado (auditoría de ticket §5): informa una opción
    # —hoy, que el platillo existe también en versión XL— sin gritarla. Mismo
    # papel que `hero-nota` (§6.29) pero dentro de una ficha o fila.
    nota = f'<p class="item-nota">{tx(it["nota"])}</p>' if it.get("nota") else ""
    if not con_precio:
        return f"{per}{desc}{nota}"
    return f"{per}{desc}{nota}<div>{precio_html(it)}</div>"
