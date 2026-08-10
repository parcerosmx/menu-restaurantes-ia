"""bloques — extraído de `build_menu.py`.

⚠️ El REPARTO de este archivo lo genera `herramientas/partir_build_menu.py`.
   Si algo está en el módulo equivocado, se ajusta el MANIFIESTO del
   splitter y se vuelve a correr — no se mueve a mano.
   El CONTENIDO (platillos, precios, textos) sí se edita aquí.
"""
from html import escape

from .iconos import (BANDERA_CO, BANDERA_MX, BOTELLA, CAM, CHISPA, SHOT_COPA)
from .idioma import tnx, tx
from .rutas import src_de

# ---------- PÁGINA DE APUESTAS (§6.37) ----------
# Alternativa al HERO de un solo producto, para hojas donde no hay UN
# protagonista sino VARIAS categorías que el dueño quiere empujar. Hoy solo
# la usa Bebidas. Cada apuesta muestra el producto que YA existe y, debajo,
# los peldaños que faltan de su escalera de ticket (marcados pendientes).
def cabecera_bloque(b, chico=False):
    """Cabecera común a los bloques de la página izquierda.
    §6.49: además del rótulo y el título admite una FRASE de categoría — el
    storytelling de una línea. Va entre el título y la nota de formato, que es
    donde el ojo ya está después de leer el nombre de la sección."""
    cls = "bloque-titulo bloque-titulo-chico" if chico else "bloque-titulo"
    ante = (f'<p class="apuesta-cat">{CHISPA}{tx(b["cat"])}</p>'
            if b.get("cat") else "")
    tit = f'<p class="{cls}">{tx(b["titulo"])}</p>' if b.get("titulo") else ""
    fr = (f'<p class="bloque-frase">{tx(b["frase"])}</p>'
          if b.get("frase") else "")
    sub = f'<p class="apuesta-nota">{tx(b["nota"])}</p>' if b.get("nota") else ""
    return ante + tit + fr + sub

def tag(txt):
    """Indicador de decisión (§6.49.6). Pastilla CREMA, nunca amarilla: el
    amarillo se reserva para dirigir la atención en pocos sitios y una pastilla
    amarilla sobre foto competiría con los rótulos de sección."""
    return f'<span class="tag-dec">{tx(txt)}</span>'

def bloque_hero_jarras(b):
    """HERO de la página (§6.49.2): foto a sangre por el borde EXTERIOR y la
    categoría entera resuelta al lado en tres líneas. Los seis sabores dejan de
    ser lista vertical con precios alineados —una tabla de comparación— y pasan
    a texto corrido: el precio queda pegado a su sabor y no hay columna que
    recorrer de arriba abajo buscando el más barato."""
    pos = f' style="object-position:{b["fpos"]}"' if b.get("fpos") else ""
    sabores = "".join(
        f'<span class="jr-s"><span class="jr-n">{tnx(n)}</span>'
        f'<span class="jr-p">{escape(pr)}</span></span>'
        for n, pr in b["escalera"])
    return f'''
    <div class="apuesta bloque-jarras">
      <div class="jr-foto-wrap"><img class="jr-foto" src="{src_de(b["foto"])}"{pos} alt=""></div>
      <div class="jr-txt">
        {cabecera_bloque(b)}
        <p class="jr-sabores"><span class="jr-cab">{tx(b["esc_titulo"])}</span>{sabores}</p>
      </div>
    </div>'''

def bloque_cocteles(b):
    """Coctelería de autor (§6.49.3): UN protagonista con foto grande y texto
    sobrepuesto, y dos de acompañamiento a un tercio de su tamaño. Antes eran
    tres fichas idénticas — tres protagonistas es ninguno."""
    def foto(c, cls):
        pos = f' style="object-position:{c["fpos"]}"' if c.get("fpos") else ""
        return (f'<img class="{cls}" src="{src_de(c["foto"])}"{pos} alt="">'
                if c.get("foto") else f'<div class="{cls} ph">{CAM}foto pendiente</div>')
    h = b["hero"]
    hero = (f'<figure class="cx-hero">{foto(h, "cx-hero-foto")}'
            f'<figcaption class="cx-hero-cap">'
            f'{tag(h["tag"]) if h.get("tag") else ""}'
            f'<p class="cx-hero-n">{tnx(h["n"])}'
            f'<span class="cx-hero-p">{escape(h["precio"])}</span></p>'
            f'<p class="cx-hero-d">{tx(h["desc"])}</p></figcaption></figure>')
    secs = "".join(
        f'<div class="cx-sec">{foto(c, "cx-sec-foto")}'
        f'<p class="cx-sec-n">{tnx(c["n"])}'
        f'<span class="cx-sec-p">{escape(c["precio"])}</span></p>'
        # La descripción existía en los datos desde el primer día y NUNCA se
        # imprimía (dueño, 2026-07-28): las dos fichas con foto salían con
        # nombre y precio pelados mientras el protagonista sí se explicaba.
        + (f'<p class="cx-sec-d">{tx(c["desc"])}</p>' if c.get("desc") else "")
        + '</div>'
        for c in b["secundarios"])
    return f'''
    <div class="apuesta bloque-cocteles">
      {cabecera_bloque(b)}
      <div class="cx-grid"><div class="cx-col">{secs}</div>{hero}</div>
    </div>'''

def bloque_ligero(b):
    """Clásicos (§6.49.4): una sola columna, una línea por cóctel. Antes eran
    dos columnas con el nombre arriba y la descripción debajo — ocho líneas y
    dos ejes de lectura para cuatro productos que el cliente pide por nombre."""
    filas = "".join(
        f'<li class="cl-item"><span class="cl-n">{tnx(c["n"])}</span>'
        f'<span class="cl-p">{escape(c["precio"])}</span>'
        f'<span class="cl-d">{tx(c["desc"])}</span></li>'
        for c in b["items"])
    return f'''
    <div class="apuesta bloque-clasicos">
      {cabecera_bloque(b, chico=True)}
      <ul class="cl-lista">{filas}</ul>
    </div>'''

BANDERAS = {"co": BANDERA_CO, "mx": BANDERA_MX}


def _bando(bd):
    """Un lado del ring: cabecera dorada con bandera y país, y debajo sus dos
    shots numerados. El número no es adorno — dice en qué ORDEN llegan a la
    tabla, así que el 1-2 es Colombia y el 3-4 México, de izquierda a derecha
    igual que en la foto."""
    bandera = BANDERAS[bd["bandera"]].replace(
        'class="bandera-co"', f'class="cd-fl {bd["bandera"]}"').replace(
        'class="bandera-mx"', f'class="cd-fl {bd["bandera"]}"')
    items = "".join(f'''
        <div class="cd-item"><span class="cd-num">{n}</span>{SHOT_COPA}
          <div><p class="cd-nom">{tnx(nom)}</p>
            <p class="cd-sub">{tx(sub)}</p></div></div>'''
        for n, (nom, sub) in enumerate(bd["shots"], bd["desde"]))
    return f'''
      <div class="cd-panel">
        <div class="cd-cab">{bandera}<span class="cd-cab-t">{tx(bd["pais"])}</span></div>
        {items}
      </div>'''


def bloque_experiencia(b):
    """El Duelo (§6.49.5) — REDISEÑADO el 2026-08-01 sobre una referencia del
    dueño. Segundo foco de la página y mayor ticket de la cara izquierda.

    El bloque dejó de ser «producto con dos banderitas» y pasa a ser un
    **cartel de duelo**: dos bandos enfrentados, cada uno con su bandera, su
    país y sus dos shots numerados, y el VS en el eje. El motivo es de venta,
    no estético — el cambio a 2 contra 2 se hizo para darle al comensal
    mexicano *un bando que defender*, y el diseño anterior no lo decía en
    ninguna parte: los cuatro licores vivían enterrados en la descripción.

    ⚠️ EL MARCO VUELVE, y contradice lo que decía esta misma función («el
    marco amarillo se retira: una tarjeta se define por su masa, no por su
    contorno»). Es decisión del dueño sobre su referencia y está registrada
    como excepción de este bloque en `style-guide.md` §6.49.5-bis. No se
    replica en los otros tres bloques de la página.

    ⚠️ Tres cosas de la referencia NO se copiaron, y ninguna es criterio
    propio: el `$` del precio (§6.2, y `verificar_datos.py` para el build),
    los puntos guía con precios alineados a la derecha (§4.1, la regla más
    dura del menú) y la textura grunge del display (el sistema es Anton
    limpio). Los brochazos dorados se traducen a barras planas, que es el
    lenguaje que ya usan las pastillas y los filetes."""
    pos = f' style="object-position:{b["fpos"]}"' if b.get("fpos") else ""
    # §4.1: el precio va PEGADO a su nombre, nunca en columna ni con guías.
    botellas = "".join(f'''
          <span class="cd-bot">{BOTELLA}{tnx(n)}<b>{escape(p)}</b></span>'''
        for n, p in b["escalera"])
    specs = f'<i class="cd-sep"></i>'.join(
        f'<b>{tx(x)}</b>' if i == 0 else tx(x)
        for i, x in enumerate(b["spec"]))
    return f'''
    <div class="apuesta bloque-duelo">
      <div class="du-foto-wrap"><img class="du-foto" src="{src_de(b["foto"])}"{pos} alt=""></div>
      <div class="du-txt">
       <div class="cd-marco">
        <p class="cd-cat">{CHISPA}{tx(b["cat"])}</p>
        <p class="cd-marca">{tnx(b["n"])}</p>
        <div class="cd-ring">
          {_bando(b["bandos"][0])}
          <div class="cd-vs">VS</div>
          {_bando(b["bandos"][1])}
        </div>
        <div class="cd-pie">
          <span class="cd-precio">{escape(b["precio"])}</span>
          <div class="cd-der">
            <div class="cd-spec">{SHOT_COPA}{specs}</div>
            <span class="cd-esc-t">{tx(b["esc_titulo"])}</span>
            <div class="cd-bots">{botellas}</div>
          </div>
        </div>
       </div>
      </div>
    </div>'''

def apuestas(a):
    """Página izquierda de Bebidas (§6.49). Cada bloque tiene su propio
    montaje: el mismo esquema repetido cuatro veces era lo que hacía que los
    cuatro pesaran igual, y una página donde todo pesa igual no tiene
    jerarquía. Aquí el reparto es HERO → segundo foco → apoyo → consulta."""
    montaje = {"hero_jarras": bloque_hero_jarras, "cocteles": bloque_cocteles,
               "ligero": bloque_ligero, "experiencia": bloque_experiencia}
    bloques = [montaje[b["tipo"]](b) for b in a["bloques"]]
    return f'''
<section class="page hero-page pagina-apuestas">
  <div class="hero-foto-completa">
    <div class="apuestas-inner">
      <span class="hero-tag">{tx(a["label"])}</span>
      {"".join(bloques)}
    </div>
  </div>
</section>'''

# ---------- PÁGINA PLACA (§6.53) ----------
# Tercer tipo de página izquierda del menú, junto al HERO de foto y a la
# página de apuestas de Bebidas: una PLACA de color plano reservada a arte que
# todavía no existe en el repo.
#
# Va como **placeholder marcado**, no como página decorativa (regla "nada se
# inventa" de CLAUDE.md): mientras la ilustración no llegue, el render dice en
# la propia página qué falta y con qué specs, y el marcador cae con el resto de
# `.pendiente` en el barrido de cierre (bloqueante 6 de ESTADO.md).
# ⚠️ Negro a plancha en offset: la imprenta tiene que confirmar el rich black
# (no 100% K solo) o la página sale gris pizarra al lado de la foto del vecino.
#
# §6.55 (2026-07-28): la placa admite ARTE montado a sangre. Mientras el arte
# sea un BOCETO —hoy, una ilustración generada con IA a 135 dpi— la página
# conserva un marcador `.pendiente` en la esquina: se puede juzgar el diseño en
# su sitio sin que un boceto se cuele en el PDF de imprenta por descuido.
def placa(p):
    if p.get("arte"):
        marca = (f'<span class="placa-boceto pendiente">{tx(p["boceto"])}</span>'
                 if p.get("boceto") else "")
        # §6.56: el rótulo NO va quemado en la imagen. El original traía
        # "BOOM! / NO PASARÄS!" generado por IA, con la Á rota. Se borró con
        # `limpiar_rotulo.py` y se vuelve a poner aquí, en Anton: así se puede
        # corregir, escala sin pixelarse y entra en el sistema tipográfico.
        rot = ""
        if p.get("rotulo"):
            rot = "".join(
                f'<span class="placa-rotulo r{i+1}">{tx(t)}</span>'
                for i, t in enumerate(p["rotulo"]))
        return f'''
<section class="page pagina-placa con-arte">
  <img class="placa-arte" src="{src_de(p["arte"])}" alt="">
  <span class="hero-tag">{tx(p["label"])}</span>
  {rot}{marca}
</section>'''
    return f'''
<section class="page pagina-placa">
  <span class="hero-tag">{tx(p["label"])}</span>
  <div class="placa-ph">
    {CAM}
    <p class="placa-ph-t">{tx(p["ph"])}</p>
    <p class="placa-ph-d">{tx(p["specs"])}</p>
  </div>
</section>'''

# ---------- ESCENA DE LA HOJA INFANTIL (§6.57) ----------
# El dueño: "esta hoja se debe salir de todo el estilo gráfico; el objetivo es
# comunicarle al NIÑO, vender diversión — está muy cuadriculada".
# Tenía razón y se veía en el render: la izquierda explota y la derecha eran
# tres filas idénticas, foto-izquierda/texto-derecha, tres veces. Al lado de la
# caricatura parecía una tabla.
#
# Lo que entra de la referencia que compartió: zigzag, marcos orgánicos con
# borde, camino punteado que guía el recorrido, sellos redondos de "incluye",
# fondo con garabatos y mascotas de personaje.
# Lo que NO entra: el precio en estallido con "$". Es la regla más citada del
# proyecto (§4) y aquí además juega en contra — el que paga es el papá, y esta
# es justo la hoja donde no conviene que lo primero que se lea sea el número.
#
# 📌 Las mascotas son **arte del dueño, píxel a píxel**: stickers circulares
# recortados de su propia caricatura con `render/stickers_infantil.py`. No se
# generó ni se redibujó ningún personaje.
def escena_infantil():
    # Garabatos de fondo en azul al 7%: nubes, estrellas, huellas y una línea
    # de ciudad. La ciudad no es un adorno cualquiera — es la que aparece
    # destruida en la caricatura de enfrente: el pliego cuenta lo mismo por los
    # dos lados. Van en SVG inline (nunca emoji, §2.1) y en un solo color.
    garabatos = '''
<svg class="inf-doodles" viewBox="0 0 192 285" preserveAspectRatio="none"
     xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor"
     stroke-width="0.7" stroke-linecap="round" stroke-linejoin="round">
  <path d="M18 34 q3-5 8-3 q2-6 8-4 q5-4 8 3 q6 0 5 5 H18 q-3 0-3-3z"/>
  <path d="M150 62 q2-4 6-2 q2-5 6-3 q4-3 6 3 q5 0 4 4 h-24 q-2 0-2-2z"/>
  <path d="M28 196 q2-4 6-2 q2-5 6-3 q4-3 6 3 q5 0 4 4 H30 q-2 0-2-2z"/>
  <path d="M166 150 l2-5 2 5 5 2-5 2-2 5-2-5-5-2z"/>
  <path d="M24 92 l1.6-4 1.6 4 4 1.6-4 1.6-1.6 4-1.6-4-4-1.6z"/>
  <path d="M172 232 l1.6-4 1.6 4 4 1.6-4 1.6-1.6 4-1.6-4-4-1.6z"/>
  <ellipse cx="150" cy="196" rx="2.4" ry="3"/><ellipse cx="156" cy="192" rx="1.7" ry="2.1"/>
  <ellipse cx="161" cy="195" rx="1.7" ry="2.1"/><ellipse cx="164" cy="201" rx="1.7" ry="2.1"/>
  <ellipse cx="30" cy="130" rx="2.4" ry="3"/><ellipse cx="36" cy="126" rx="1.7" ry="2.1"/>
  <ellipse cx="41" cy="129" rx="1.7" ry="2.1"/><ellipse cx="44" cy="135" rx="1.7" ry="2.1"/>
  <path d="M0 268 h14 v-20 h10 v-13 h12 v24 h9 v-31 h13 v31 h11 v-18 h14 v18 h10 v-27 h12 v27
           h11 v-15 h13 v15 h10 v-22 h11 v22 h12 v-16 h13 v16 h12"/>
  <path d="M26 250 h4 v4 h-4z M40 240 h4 v4 h-4z M74 236 h4 v4 h-4z M106 246 h4 v4 h-4z
           M140 244 h4 v4 h-4z M170 240 h4 v4 h-4z"/>
</svg>'''
    # Camino punteado: rompe la retícula sin mover ni un platillo de sitio.
    # Es UNA sola curva que cruza la hoja entera y va POR DEBAJO de las fotos,
    # así que solo asoma en los huecos — se lee como un rastro continuo que
    # pasa por detrás. Se probó con dos tramos cortos entre filas y no cabían:
    # el corredor libre entre una fila y la siguiente son 6mm.
    camino = '''
<svg class="inf-camino" viewBox="0 0 192 285" preserveAspectRatio="none"
     xmlns="http://www.w3.org/2000/svg" fill="none">
  <defs>
    <marker id="pta" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="5"
            markerHeight="5" orient="auto-start-reverse">
      <path d="M0 1 L9 5 L0 9z" fill="currentColor"/>
    </marker>
  </defs>
  <path d="M55 108 C 80 120, 90 122, 101 126" stroke="currentColor" stroke-width="1.2"
        stroke-dasharray="3.2 3.6" stroke-linecap="round" marker-end="url(#pta)"/>
  <path d="M148 178 C 120 190, 92 184, 68 187" stroke="currentColor" stroke-width="1.2"
        stroke-dasharray="3.2 3.6" stroke-linecap="round" marker-end="url(#pta)"/>
</svg>'''
    # Marcas de impacto de cómic junto a cada foto: tres trazos que salen
    # disparados de la esquina. Es el gesto que a la referencia le daba
    # "aventura" y no cuesta ni un milímetro de contenido.
    chispazos = '''
<svg class="inf-pow inf-pow-1" viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg"
     fill="none" stroke="currentColor" stroke-width="4.5" stroke-linecap="round">
  <path d="M20 34 L20 12"/><path d="M6 30 L2 14"/><path d="M33 29 L38 14"/>
</svg>
<svg class="inf-pow inf-pow-2" viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg"
     fill="none" stroke="currentColor" stroke-width="4.5" stroke-linecap="round">
  <path d="M20 34 L20 12"/><path d="M6 30 L2 14"/><path d="M33 29 L38 14"/>
</svg>
<svg class="inf-pow inf-pow-3" viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg"
     fill="none" stroke="currentColor" stroke-width="4.5" stroke-linecap="round">
  <path d="M20 34 L20 12"/><path d="M6 30 L2 14"/><path d="M33 29 L38 14"/>
</svg>'''
    # §6.66-bis — las mascotas conservan su sombra en el propio `filter`, con
    # el coste de resolución medido y aceptado. El porqué, en menu-v2.css.
    mascotas = (
        f'<img class="inf-masc inf-masc-perro" src="{src_de("infantil/masc-perrito.png")}" alt="">'
        f'<img class="inf-masc inf-masc-pato" src="{src_de("infantil/masc-patochef.png")}" alt="">')
    return garabatos + camino + chispazos + mascotas
