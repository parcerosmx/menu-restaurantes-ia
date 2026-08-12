"""hero — extraído de `build_menu.py`.

⚠️ El REPARTO de este archivo lo genera `herramientas/partir_build_menu.py`.
   Si algo está en el módulo equivocado, se ajusta el MANIFIESTO del
   splitter y se vuelve a correr — no se mueve a mano.
   El CONTENIDO (platillos, precios, textos) sí se edita aquí.
"""
from html import escape

from .enganches import adic_linea, adic_lista_html
from .iconos import CORAZON, ESTRELLA, ICO_PERSONAS, bullets
from .idioma import t, tn, ts, tx
from .rutas import src_de

def hero(h):
    if h.get("foto"):
        f = h["foto"]
        bg = f'<img class="hero-foto-img" src="{src_de(f)}" alt="">'
        pagecls = "hero-page hero-oscuro" if h.get("oscuro") else "hero-page"
        if h.get("realce"):
            pagecls += " hero-realce"
        # §6.34: foto ya corregida y comprimida a gama CMYK en el archivo.
        # Anula el filter de `realce` — volver a saturar por CSS desharía la
        # corrección y devolvería los naranjas fuera de gama.
        if h.get("cmyk"):
            pagecls += " hero-cmyk"
        # §6.30 (2026-07-26): SIN sello en ningún hero hasta que el dueño
        # diseñe uno propio — el SVG genérico de arriba queda en reserva.
        sello = ""
    else:
        bg = ""
        pagecls = "hero-page hero-ph"
        sello = ""
    # Gancho de clase por hoja (§6.52): la página derecha ya podía pedir su
    # propio tratamiento con "cls", pero el HERO no tenía dónde engancharlo y
    # cualquier ajuste de ritmo se aplicaba a las seis portadillas a la vez.
    if h.get("cls"):
        pagecls += f' {h["cls"]}'
    partes = tn(h["nombre"]).split("|")
    nombre = f'<p class="hero-display">{escape(partes[0])}</p>'
    if len(partes) > 1:
        # n2_display (§6.29): la 2.ª palabra del nombre en el MISMO display
        # que la 1.ª (solo cambia el color) cuando forma parte del nombre
        # propio del platillo — el script queda para apellidos decorativos.
        if h.get("n2_display"):
            nombre += f'<p class="hero-display hero-display-sub">{escape(partes[1])}</p>'
        else:
            nombre += f'<p class="hero-script">{escape(partes[1])}</p>'
    pre = ""
    if h.get("pre"):
        if "·" in h["pre"]:
            # Una sola línea: kg en script · icono personas + caps (§6.21)
            script, caps = ts(h["pre"], "·")
            pre = (f'<p class="hero-pre-linea"><span class="hpl-script">{escape(script)}</span>'
                   f'<span class="hpl-sep">·</span>{ICO_PERSONAS}'
                   f'<span class="hpl-caps">{escape(caps)}</span></p>')
        else:
            pre = f'<p class="hero-unidades">{tx(h["pre"])}</p>'

    # 🇨🇴 Glosa del NOMBRE (§5.1-ter, 2026-07-30). Va pegada al nombre porque
    # lo que traduce es el nombre — no el plato: si bajara al panel de la
    # esquina, el lector la encontraría después de haber decidido si le
    # interesa. No usa el panel `hero-glosa` a propósito: ese slot es el mismo
    # que el del maridaje, y §5.1-bis dice que admite uno solo.
    if h.get("glosa_nombre"):
        pre = f'<p class="hero-glosa-nombre">{tx(h["glosa_nombre"])}</p>' + pre

    if h.get("bullets"):
        cuerpo = f'<ul class="hero-lista">{bullets(h["bullets"])}</ul>'
    else:
        cuerpo = '<p class="hero-lista-pend">descripción pendiente</p>'
    # Remate estrella (§6.21): frase de experiencia entre bullets y precio
    punch = (f'<p class="hero-punch"><span class="punch-star">{ESTRELLA}</span>'
             f'{tx(h["punch"])}</p>'
             if h.get("punch") else "")
    if h.get("precio"):
        # §6.66 — la sombra va en su PROPIA capa, no en un `filter` sobre la
        # pastilla. Un `filter` obliga a Chromium a rasterizar el elemento
        # entero al generar el PDF: el precio del hero salía como mapa de bits
        # a 277 dpi en las cuatro hojas que lo llevan, en vez de texto
        # vectorial. Con la sombra en un hermano, el número sigue siendo texto.
        # La capa va vacía y `aria-hidden`: es pintura, no contenido.
        precio = ('<div class="hero-precio-caja">'
                  '<span class="hero-precio-sombra" aria-hidden="true"></span>'
                  f'<p class="hero-precio">{escape(h["precio"])}</p></div>')
    else:
        precio = '<p class="hero-precio-pendiente">precio pendiente</p>'
    pill = f'<div><span class="pill-nota">{tx(h["pill"])}</span></div>' if h.get("pill") else ""
    # Nota discreta (§6.29): informa una opción sin gritarla — texto pequeño
    # en crema, sin fondo (el pill azul queda para notas que sí deben llamar).
    nota = f'<p class="hero-nota">{tx(h["nota"])}</p>' if h.get("nota") else ""
    # 🌶️ Adiciones del hero EN LÍNEA, no en panel (§6.30-quinquies-bis,
    # 2026-08-05). Tercera forma de decir "agrégale más sabor", y existe por una
    # colisión física, no por gusto: el panel `hero-adiciones` y la glosa
    # comparten la esquina inferior derecha (§5.1: uno u otro, nunca los dos), y
    # el hero de Entradas ya gasta ese hueco en la glosa aprobada del patacón.
    # Sin esta variante, meterle adiciones al Chicharrón Trancao obligaba a
    # elegir entre las dos — o a inventarle un slot nuevo al hero.
    #
    # Reusa `adic_linea()` entero, que es lo que importa: el precio sigue
    # saliendo del catálogo ADICIONES y no se teclea aquí (§8.1). Lo único
    # propio es el color, que lo pone `.hero-page .adic-linea` en el CSS — la
    # línea del listado va en oscuro sobre pastel y aquí va sobre una foto.
    # Cae donde caía la nota, dentro del scrim, para no estrenar posición.
    adic_lin = (adic_linea(h["adic_lin"], h.get("adic_rot", "Agrégale más sabor"))
                if h.get("adic_lin") else "")
    # Glosa de término colombiano (PROPUESTA 2026-07-26): se explica UNA vez
    # en la hoja donde el término es protagonista; el resto del menú solo usa
    # la palabra. Copy pendiente de aprobación del dueño.
    # Adiciones contextuales (§6.30-quinquies): upsell en el punto de
    # decisión. Los nombres y precios ya NO se escriben aquí — son claves del
    # catálogo ADICIONES, que es la fuente única (auditoría de ticket §10.3):
    # antes el mismo precio vivía en el hero y en la tabla de cierre y podía
    # quedar distinto en dos páginas del mismo menú.
    adic = ""
    if h.get("adiciones"):
        adic = ('<div class="hero-adiciones">'
                f'<p class="adic-titulo">{tx("Agrégale más sabor")}</p>'
                f'<ul class="adic-lista">{adic_lista_html(h["adiciones"])}</ul></div>')
    # 🍹 MARIDAJE (§6.65, 2026-07-30) — misma esquina y misma anatomía que el
    # panel de adiciones, y por eso son EXCLUYENTES: los dos ocupan el hueco
    # inferior derecho del HERO, y dos paneles ahí competirían entre sí (A3
    # señal 6). Un HERO propone adición **o** bebida, nunca las dos cosas.
    #
    # La diferencia que justifica una variante y no reusar el bloque tal cual:
    # una adición se suma al plato y su precio se escribe **+90**; una bebida es
    # OTRO producto, con su propio precio. Imprimir "+140" sobre un refajo diría
    # que la bebida es un extra de la hamburguesa, que es falso y además
    # invitaría a sumarlo mentalmente al 270.
    if h.get("maridaje"):
        m = h["maridaje"]
        filas = "".join(
            f'<li><span class="adic-n">{escape(n)}</span>'
            f'<span class="adic-p">{escape(p)}</span></li>'
            for n, p in m["items"])
        adic = (f'<div class="hero-adiciones hero-maridaje">'
                f'<p class="adic-titulo">{tx(m["t"])}</p>'
                f'<ul class="adic-lista">{filas}</ul>'
                + (f'<p class="maridaje-pie">{tx(m["pie"])}</p>'
                   if m.get("pie") else "") + '</div>')
    glosa = ""
    if h.get("glosa"):
        glosa = (f'<div class="hero-glosa"><p class="glosa-titulo">{tx(h["glosa"]["t"])}</p>'
                 f'<p class="glosa-texto">{tx(h["glosa"]["d"])}</p></div>')
    return f'''
<section class="page {pagecls}">
  <div class="hero-foto-completa">
    {bg}
    <div class="hero-overlay-scrim">
      <span class="hero-tag">{tx(h["label"])}</span>
      {nombre}
      {pre}{cuerpo}{punch}{precio}{pill}{nota}{adic_lin}
    </div>
    {sello}{glosa}{adic}
  </div>
</section>'''

def pie():
    """El lema de la marca al pie de cada hoja de listado.

    ⚠️ El lema lo pone el TEMA, no este archivo. Estaba escrito aquí —«De
    corazón y sabor.», con el corazón de Parceros— y **la primera vez que se
    arregló, el arreglo se perdió al copiar el motor de un repo al otro**. Se
    volvió a encontrar montando una panadería con `menu-ia crear`: su carta
    salió firmada con el lema de un restaurante colombiano.

    Es invisible para toda guarda del cliente original: la cadena escrita a
    mano ES su lema, así que sus PNG salen idénticos y `comprobar` da verde.
    Solo lo destapa un cliente NUEVO — que es justo para lo que sirve tener
    uno de demostración.

    Un tema sin lema no pinta pie. Nada de copy inventado, aquí tampoco.
    """
    from .. import tema as _tema
    lema = _tema.ACTIVO.lema
    if not lema:
        return ""
    return f'<div class="pie">{_tema.ACTIVO.ornamento("pie_ico")}{tx(lema)}</div>'
