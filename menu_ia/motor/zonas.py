"""zonas — extraído de `build_menu.py`.

⚠️ El REPARTO de este archivo lo genera `herramientas/partir_build_menu.py`.
   Si algo está en el módulo equivocado, se ajusta el MANIFIESTO del
   splitter y se vuelve a correr — no se mueve a mano.
   El CONTENIDO (platillos, precios, textos) sí se edita aquí.
"""
from html import escape

from .enganches import adic_linea
from .iconos import CAM, ESTRELLA
from .idioma import tx
from .piezas import cuerpo_html, nombre_html
from .enganches import precio_bebida, precio_jarra_min, precio_postre
from .rutas import src_de

# ---------- zonas ----------

def zona_feat(it):
    # Un solo favorito por página, con sello discreto (§6.16.3)
    sello = f'<span class="feat-sello">{tx("El")}<br>{tx("favorito")}</span>' if it.get("fav") else ""
    if it.get("foto"):
        foto = f'<img class="feat-foto" src="{src_de(it["foto"])}" alt="">'
    else:
        foto = f'<div class="feat-foto-ph">{CAM}foto pendiente</div>'
    return f'''
    <div class="feat">
      <div class="feat-texto">{nombre_html(it)}{cuerpo_html(it)}</div>
      <div class="feat-foto-wrap">{sello}{foto}</div>
    </div>'''

def zona_media(it):
    if it.get("foto"):
        foto = f'<img class="media-foto" src="{src_de(it["foto"])}" alt="">'
        cls = "media-row"
    elif it.get("foto_pendiente"):
        foto = f'<div class="media-foto ph">{CAM}foto pendiente</div>'
        cls = "media-row"
    else:
        foto = ""
        cls = "media-row solo-texto"
    return f'''
    <div class="{cls}">
      <div>{nombre_html(it)}{cuerpo_html(it)}</div>
      {foto}
    </div>'''

def zona_flujo(items):
    """Secundarios en flujo editorial (§6.16.2): poses variadas que rotan
    (pa horizontal / pb vertical / pc compacta) — nunca cuadrícula."""
    ciclo = ["pa", "pc"]
    fichas, j = [], 0
    for it in items:
        if it.get("alta"):
            pose = "pb"          # platos verticales → foto vertical
        else:
            pose = ciclo[j % len(ciclo)]; j += 1
        if it.get("foto"):
            foto = f'<img class="flujo-foto" src="{src_de(it["foto"])}" alt="">'
        else:
            foto = f'<div class="flujo-foto ph">{CAM}foto pendiente</div>'
        fichas.append(f'<div class="flujo-item {pose}">{foto}{nombre_html(it)}{cuerpo_html(it)}</div>')
    return f'<div class="flujo">{"".join(fichas)}</div>'

def zona_favfila(it):
    """Fila favorito (§6.17.2): foto grande izq + texto der, tag cinta."""
    if it.get("foto"):
        foto = f'<img class="favfila-foto" src="{src_de(it["foto"])}" alt="">'
    else:
        foto = f'<div class="favfila-foto ph flujo-foto">{CAM}foto pendiente</div>'
    tag = f'<span class="tag-fav-cinta">{ESTRELLA}{tx("El favorito")}</span>' if it.get("fav") else ""
    # §6.56-ter: el favorito también admite adiciones, en la misma línea tenue
    # que ya usan la torre y los subgrupos de Bebidas. Nunca panel: no hay foto
    # debajo sobre la que apoyarlo y competiría con el platillo.
    adic = adic_linea(it["adic"], it.get("adic_rot", "Agrégale más sabor")) if it.get("adic") else ""
    return f'''
    <div class="favfila">
      <div class="favfila-foto-wrap">{foto}</div>
      <div>{tag}{nombre_html(it)}{cuerpo_html(it)}{adic}</div>
    </div>'''

def zona_filas(items):
    """Filas del listado (§6.17.3-4): foto generosa izq / texto con el
    precio integrado bajo la descripción (nunca al margen).
    "fav": cinta "★ El favorito" sobre la foto (washi, §6.30-bis.3) SIN
    cambiar el tamaño de la fila — excepción tipo §6.26.4."""
    filas = []
    for it in items:
        if it.get("foto"):
            # "fpos": encuadre del recorte para fotos verticales (object-position)
            pos = f' style="object-position:{it["fpos"]}"' if it.get("fpos") else ""
            foto = f'<img class="fila-foto" src="{src_de(it["foto"])}"{pos} alt="">'
        else:
            foto = f'<div class="fila-foto ph flujo-foto">{CAM}foto pendiente</div>'
        tag = f'<span class="tag-fav-cinta">{ESTRELLA}{tx("El favorito")}</span>' if it.get("fav") else ""
        # §6.54 (dueño, 2026-07-28): cinta washi de VALOR INCLUIDO — mismo
        # mecanismo que la del favorito (no gasta alto, va sobre la esquina de
        # la foto) pero en azul, para que no se lea como "★ El favorito". Hoy
        # solo la usa la Cajita Parceritos, por el patito coleccionable.
        if it.get("sello"):
            tag += f'<span class="tag-sello-cinta">{tx(it["sello"])}</span>'
        cls = "fila alta" if it.get("alta") else "fila"
        # §6.57: "zig" invierte foto y texto en esa fila. Va como DATO y no
        # como :nth-of-type porque la cabecera de sección es hermana de las
        # filas y desplaza la cuenta — el primer intento invirtió la fila 1.
        if it.get("zig"):
            cls += " fila-zig"
        if it.get("dom"):
            cls += " fila-dom"
        adic = adic_linea(it["adic"], it.get("adic_rot", "Agrégale más sabor")) if it.get("adic") else ""
        filas.append(f'''
    <div class="{cls}">
      {tag}{foto}
      <div>{nombre_html(it)}{cuerpo_html(it)}{adic}</div>
    </div>''')
    return "".join(filas)

def zona_filav(it):
    """Fila DESTACADA VERTICAL (propuesta 2026-07-26, referencia de
    distribución del dueño): texto a la izquierda y foto VERTICAL a la
    derecha usando todo el alto del bloque — para platillos de torre
    (Bandeja 3 Pisos). Distinta de la fila "alta" izquierda descartada
    en §6.23."""
    foto = f'<img class="filav-foto" src="{src_de(it["foto"])}" alt="">'
    return f'''
    <div class="filav">
      <div>{nombre_html(it)}{cuerpo_html(it)}
        {adic_linea(it["adic"], it.get("adic_rot", "Agrégale más sabor")) if it.get("adic") else ""}</div>
      <div class="filav-foto-wrap">{foto}</div>
    </div>'''

def zona_cruce_postre(it):
    """Puente hacia la hoja de POSTRES desde una hoja de plato fuerte
    (auditoría `POS-A3-001`, 2026-07-30).

    **Por qué existe.** El barrido del texto visible de las 16 páginas dio un
    dato que nadie había medido: la palabra *"postre"* aparece por primera vez
    **en la propia hoja 7**. Cero puentes desde Típicos (292 uds en 14 días),
    Entradas (211) o De la Calle (96). Y el attach rate de postre está en
    **7.3 %** — 43 postres contra 588 platos fuertes — en la hoja de **mejor
    CMV del menú (15.0 %)**.

    Es exactamente el argumento con el que el proyecto bajó el café a la hoja
    7 (*"se vende en el minuto 40, cuando esa hoja ya pasó y el menú suele
    estar recogido de la mesa"*) — **y a los postres, que están una página más
    allá, nunca se les aplicó**.

    **Por qué aquí y no en la bebida.** La recomendación de la auditoría de De
    la Calle era cruzar BEBIDA (*"una burger es el disparador de bebida más
    obvio del menú"*). Se revisa con el dato en la mano: las bebidas de esta
    casa **ya se venden solas** —jugo de lulo 236 uds, Coca-Cola 113, Corona
    72— y una línea impresa añade poco a un comportamiento automático. El
    postre no ocurre: 7.3 %. **El copy cruzado vale más donde la conducta está
    ausente que donde ya es automática.**

    **Por qué el plato fuerte y no el final.** Es el único momento en que la
    decisión sigue abierta: cuando el cliente elige la hamburguesa todavía
    tiene hambre y presupuesto. Es hipótesis de diseño, no ley (rúbrica §3.5),
    y se valida con el próximo export de EPOS contra el 7.3 % de hoy.

    El precio sale de la hoja 7 (`precio_postre`), nunca se teclea."""
    return (f'<p class="cruce-linea cruce-postre">{tx(it["t"])}'
            f'<span class="cruce-p">{escape(precio_postre(it["postre"]))}</span></p>')

def zona_cruce_mesa(it):
    """Banda «Para la mesa» al pie del listado (§6.63, dueño 2026-07-30).

    Quien pide un platillo de esta hoja **viene en grupo**, y hasta hoy la
    única bebida cruzada aquí era una cerveza SUELTA (60) en la nota de la
    Picada. El dueño: *"si hay un cliente interesado en pedir esos platillos es
    porque viene en grupo grande… no recomiendes bebida por unidad, estamos
    perdiendo una oportunidad"*. Se cruzan los dos productos de MESA que ya
    existen en Bebidas —jarra (4 vasos) y Cubetazo (5 cervezas)— y desaparece
    la línea de cerveza por unidad.

    Anatomía = el cierre tipográfico a 2 columnas de Entradas (filete superior
    + dos ítems), que ya está declarada: la hoja no estrena una forma, reusa
    una. Los precios salen de la carta de Bebidas, nunca se teclean aquí."""
    jarra, cubeta = precio_jarra_min(), precio_bebida("Cubetazo")
    return f"""
    <div class="cruce-mesa">
      <p class="cruce-mesa-t">{tx(it["t"])}</p>
      <div class="cruce-mesa-items">
        <p><span class="cm-n">{tx("Jarra de jugo")}</span> <span class="cm-d">{tx("para 4 vasos")}</span><span class="cm-p">{tx("desde")} {jarra}</span></p>
        <p><span class="cm-n">{tx("Cubetazo")}</span> <span class="cm-d">{tx("cinco cervezas en cubeta")}</span><span class="cm-p">{cubeta}</span></p>
      </div>
    </div>"""

def zona_cruce(it):
    """Línea de venta cruzada al pie de una hoja (§6.62).

    La auditoría de la hoja infantil (`investigacion/auditoria-hoja-infantil.md`,
    hallazgo INF-A3-001) encontró que era el único pliego sin ningún cruce — y
    justo el que más lo pedía: la orden del niño y la de las bebidas se toman en
    la MISMA vuelta del mesero, que fue el argumento para ponerlo en posición 2.
    El precio no se teclea aquí: sale de la carta de Bebidas."""
    return (f'<p class="cruce-linea">{tx(it["t"])}'
            f'<span class="cruce-p">{escape(precio_bebida(it["bebida"]))}</span></p>')

def zona_banda(it):
    """Banda de colección de patitos (§6.60).

    Sustituye al sello redondo "1 de 30 patitos coleccionables", que el dueño
    tumbó: *"se ve aburrido y además tapa el patito de la foto"*. Tenía las dos
    razones. Un número no se colecciona — **una repisa llena de patitos sí**—, y
    el sello caía justo encima del único patito que enseñaba la foto, que era lo
    que sostenía la promesa.

    La imagen es un recorte de la foto de catálogo del dueño con el fondo
    blanco quitado (`render/recortar_patitos.py`), NO patitos generados."""
    return f'''
    <div class="patitos-banda">
      <div class="patitos-marco"><img class="patitos-img" src="{src_de(it["foto"])}" alt=""></div>
      <div class="patitos-txt">
        <p class="patitos-t">{tx(it["t"])}</p>
        <p class="patitos-d">{tx(it["d"])}</p>
      </div>
    </div>'''

def zona_texto(items):
    fichas = "".join(f'<div class="texto-item">{nombre_html(it)}{cuerpo_html(it)}</div>'
                     for it in items)
    return f'<div class="texto-fila">{fichas}</div>'

def zona_texto_ancho(items):
    """Platillos sin foto a ANCHO COMPLETO, 1 sola columna (§6.25):
    mismos texto-item apilados, cada uno ocupando toda la caja."""
    fichas = "".join(f'<div class="texto-item">{nombre_html(it)}{cuerpo_html(it)}</div>'
                     for it in items)
    return f'<div class="texto-lista">{fichas}</div>'

def zona_grupofoto(items):
    """Grupo con foto(s) compartida(s) (§6.33): platillos con la misma
    presentación (la arepa se ve igual; cambia el relleno). Cabecera de
    foto a todo el ancho del grupo — "gfoto" sola, o "gfoto"+"gfoto2"
    en dúo (plato + interacción). Alternativa: sin gfoto, cada item con
    su mini "ifoto" arriba del texto. Textos en columnas con filetes."""
    it0 = items[0]
    cab = ""
    if it0.get("gfoto"):
        fotos = f'<img class="fila-foto grupofoto-img" src="{src_de(it0["gfoto"])}" alt="">'
        if it0.get("gfoto2"):
            fotos += f'<img class="fila-foto grupofoto-img" src="{src_de(it0["gfoto2"])}" alt="">'
        cab = f'<div class="grupofoto-fotos">{fotos}</div>'
    def ficha(it):
        mini = (f'<img class="fila-foto item-foto" src="{src_de(it["ifoto"])}" alt="">'
                if it.get("ifoto") else "")
        return f'<div class="grupofoto-item">{mini}{nombre_html(it)}{cuerpo_html(it)}</div>'
    textos = "".join(ficha(it) for it in items)
    return f'<div class="grupofoto">{cab}<div class="grupofoto-textos">{textos}</div></div>'

def ficha_card(it):
    """Ficha foto-arriba (§6.25): foto a todo el ancho de la columna,
    debajo nombre + descripción + precio.
    "cuadrada": foto 1:1 dominante (§6.26 Típicos). "fav": cinta de
    favorito sobre el texto, sin alterar el tamaño de la ficha."""
    sq = " cuadrada" if it.get("cuadrada") else ""
    if it.get("foto"):
        pos = f' style="object-position:{it["fpos"]}"' if it.get("fpos") else ""
        foto = f'<img class="fila-foto card-foto{sq}" src="{src_de(it["foto"])}"{pos} alt="">'
    else:
        foto = f'<div class="fila-foto card-foto{sq} ph flujo-foto">{CAM}foto pendiente</div>'
    tag = f'<span class="tag-fav-cinta">{ESTRELLA}{tx("El favorito")}</span>' if it.get("fav") else ""
    return f'<div class="card">{foto}{tag}{nombre_html(it)}{cuerpo_html(it)}</div>'

def zona_cards(items):
    """Cuadrícula de fichas iguales a 2 columnas (§6.25): con 4 fichas
    fluye a 2×2 — mismo peso jerárquico para todas.
    (La zona mixta texto+foto de la 1.ª propuesta se eliminó con ella.)"""
    return f'<div class="grid2">{"".join(ficha_card(it) for it in items)}</div>'

def listado(items):
    # Mismo convenio que los pliegos (ver ACTIVOS más abajo): un platillo con
    # "activo": False conserva aquí su texto, precio y foto pero no se maqueta.
    # Sirve para sacar un platillo del menú sin perder lo ya decidido.
    items = [it for it in items if it.get("activo", True)]
    out, grupo, i = [], None, 0
    while i < len(items):
        it = items[i]
        if it.get("g") and it["g"] != grupo:
            grupo = it["g"]
            out.append(f'<p class="mini-titulo">{tx(grupo)}</p>')
            # Adiciones del SUBGRUPO (auditoría de ticket §10.1): el bloque
            # del hero solo puede servir a un platillo, pero hay familias
            # enteras que disparan las mismas adiciones — las sopas se
            # completan con consomé, arepa y pechuga. Una línea, en el
            # sistema tenue de los modificadores.
            if it.get("g_adic"):
                out.append(adic_linea(it["g_adic"]))
        rol = it.get("rol", "media")
        if rol in ("flujo", "texto", "textoancho", "fila", "card", "grupofoto"):
            lote = [it]
            while (i + 1 < len(items) and items[i+1].get("rol") == rol
                   and items[i+1].get("g") == it.get("g")):
                i += 1
                lote.append(items[i])
            out.append({"flujo": zona_flujo, "texto": zona_texto,
                        "textoancho": zona_texto_ancho,
                        "fila": zona_filas, "card": zona_cards,
                        "grupofoto": zona_grupofoto}[rol](lote))
        elif rol == "cruce":
            out.append(zona_cruce(it))
        elif rol == "banda":
            out.append(zona_banda(it))
        elif rol == "feat":
            out.append(zona_feat(it))
        elif rol == "favfila":
            out.append(zona_favfila(it))
        elif rol == "filav":
            out.append(zona_filav(it))
        elif rol == "cruce_mesa":
            out.append(zona_cruce_mesa(it))
        elif rol == "cruce_postre":
            out.append(zona_cruce_postre(it))
        else:
            out.append(zona_media(it))
        i += 1
    return "".join(out)


# ════════════════════════════════════════════════════════════════════════
#  Listado DENSO — el del arquetipo «hoja» (Fase 3)
# ════════════════════════════════════════════════════════════════════════
def listado_denso(items):
    """Nombre, descripción y precio. Sin fotos, sin zonas, sin portadilla.

    `listado()` despacha sobre trece roles y **todos** montan una caja con
    foto: son las zonas que dan el recorrido visual de un pliego. En una hoja
    suelta no hay recorrido que dar —hay una cara y hay que caber—, así que
    los roles se ignoran a propósito y todo baja al mismo renglón.

    Se conservan las dos cosas que son contenido y no maqueta:
      · los subgrupos (`g`), que ordenan la carta para quien la lee;
      · el convenio de `activo`, para dar de baja sin perder lo decidido.

    ⚠️ **El precio sigue sin ir en columna alineada.** Es donde más tienta
    romperlo —en una lista apretada, alinear «ordena»— y es justo lo que
    convierte la carta en un comparador de precios. Va pegado al nombre, igual
    que en el pliego.
    """
    items = [it for it in items if it.get("activo", True)]
    out, grupo = [], None
    for it in items:
        if it.get("g") and it["g"] != grupo:
            grupo = it["g"]
            out.append(f'<p class="mini-titulo">{tx(grupo)}</p>')
            if it.get("g_adic"):
                out.append(adic_linea(it["g_adic"]))
        out.append('<div class="denso-item">'
                   f'{nombre_html(it)}{cuerpo_html(it)}</div>')
    return '<div class="lista-densa">' + "".join(out) + "</div>"
