"""iconos — extraído de `build_menu.py`.

⚠️ El REPARTO de este archivo lo genera `herramientas/partir_build_menu.py`.
   Si algo está en el módulo equivocado, se ajusta el MANIFIESTO del
   splitter y se vuelve a correr — no se mueve a mano.
   El CONTENIDO (platillos, precios, textos) sí se edita aquí.
"""
from html import escape
from .idioma import tx

# §2.1 — el ✓ de los bullets del hero y el ♥ del pie van como SVG INLINE.
# No es una preferencia de estilo: **Poppins no tiene ninguno de los dos**, así
# que el navegador los sacaba de una fuente del sistema — el ✓ de Lucida Grande
# y el ♥ de Arial. Eso metía tres problemas en un impreso comercial:
#   1. la forma del glifo cambiaba según la máquina que generase el menú;
#   2. el PDF acababa con una fuente de sistema incrustada, con su licencia;
#   3. no había forma de ajustar grosor ni color de marca.
# En SVG son nuestros, escalan sin pixelarse y separan a CMYK como el resto.
TICK = ('<svg class="tick" viewBox="0 0 16 16" fill="none" aria-hidden="true" '
        'xmlns="http://www.w3.org/2000/svg">'
        '<path d="M2.6 8.6 6.3 12.4 13.4 3.9" stroke="currentColor" '
        'stroke-width="2.7" stroke-linecap="round" stroke-linejoin="round"/>'
        '</svg>')

# §2.1 — la ★ también es SVG. Mismo caso que el ✓ y el ♥: Poppins no la tiene,
# así que salía de una fuente de sistema (y Chromium acababa metiéndola en el
# PDF como una fuente Type3 sin nombre). Los cinco vértices están calculados,
# no dibujados a ojo: radio exterior 7.7 e interior 3.35 sobre una caja de 16,
# que es la proporción del glifo tipográfico al que sustituye.
ESTRELLA = ('<svg class="estrella" viewBox="0 0 16 16" aria-hidden="true" '
            'xmlns="http://www.w3.org/2000/svg">'
            '<path d="M8.00 0.30 L9.97 5.29 L15.32 5.62 L11.19 9.04 L12.53 14.23 '
            'L8.00 11.35 L3.47 14.23 L4.81 9.04 L0.68 5.62 L6.03 5.29 Z" '
            'fill="currentColor"/></svg>')

CORAZON = ('<svg class="corazon" viewBox="0 0 16 16" aria-hidden="true" '
           'xmlns="http://www.w3.org/2000/svg">'
           '<path d="M8 14.3C8 14.3 1.2 10.1 1.2 5.5 1.2 3.1 3 1.5 5 1.5 '
           '6.4 1.5 7.4 2.3 8 3.3 8.6 2.3 9.6 1.5 11 1.5 13 1.5 14.8 3.1 '
           '14.8 5.5 14.8 10.1 8 14.3 8 14.3Z" fill="currentColor"/>'
           '</svg>')

def bullets(xs):
    return "".join(f"<li>{TICK}{tx(b)}</li>" for b in xs)

# §6.30-quater: hojita junto a "guascas" (Ajiaco). SVG inline en naranja de
# marca — nunca el emoji de sistema (RGB, no separa a CMYK). Se escribe en el
# texto como el token [[hoja]] y se sustituye después de escapar.
HOJA = ('<svg class="hoja-glosa" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
        # tallo casi vertical (el eje es lo que evita que se lea como ✓)
        '<path d="M8.4 15.2C8.4 12.4 7.9 9.2 7.7 6.2" stroke="currentColor" stroke-width="1.25" stroke-linecap="round"/>'
        # hoja de la punta
        '<path d="M7.7 6.4C7.4 4 8.5 1.8 10.3 0.9 11.1 3.1 10.4 5.5 8.6 6.7 8.2 7 7.7 6.9 7.7 6.4Z" fill="currentColor"/>'
        # hoja derecha
        '<path d="M8 8.7C9 6.7 11 5.4 13.5 5.2 13.3 7.7 11.4 9.5 8.8 9.5 8.1 9.5 7.8 9.3 8 8.7Z" fill="currentColor"/>'
        # hoja izquierda, más abajo
        '<path d="M7.8 11.5C6.8 9.7 5 8.7 2.7 8.7 2.9 11 4.6 12.6 7 12.5 7.6 12.5 7.9 12.1 7.8 11.5Z" fill="currentColor"/>'
        '</svg>')

# Bandera de Colombia junto a los licores colombianos (dueño 2026-07-27,
# sustituye a la pastilla "Colombiano"). SVG inline, NUNCA el emoji 🇨🇴: los
# emoji son RGB y no separan a CMYK — misma regla que la hojita de guascas
# (§6.30-quater). Proporción 3:2 y bandas 1/2 · 1/4 · 1/4 como la real.
# Segunda excepción controlada a la paleta, junto con el verde de la guasca:
# una bandera solo se reconoce con sus colores.
# 🦆 Patito de la etiqueta "Para niños" (§6.63). SVG inline, NUNCA emoji: los
# emoji son RGB, no separan a CMYK y arrastran el negro del sistema (§2.1).
# Por qué un patito y no una silueta de niño: el patito coleccionable YA es el
# símbolo de lo infantil en este menú —puebla la caricatura del pliego 2 y su
# banda de colección—, así que la etiqueta no estrena un signo, reutiliza uno
# que el cliente ya vio dos páginas antes.
# Una sola tinta (currentColor): la paleta son 4 colores planos y un patito a
# dos tintas pediría una quinta.
# 2026-07-29 — REDIBUJADO. La primera versión vivía dentro de una pastilla con
# la palabra "PARA NIÑOS" al lado, así que no tenía que explicarse sola: bastaba
# con que se leyera "bicho amarillo". Ahora el patito va SOLO, y a 4 mm sobre
# papel tiene que decir "pato" sin ayuda. Qué cambió y por qué:
#   · más grande y con la cabeza más arriba, para que se vean DOS masas —cuerpo
#     y cabeza— y no un solo bulto. Se tocan apenas: ese pellizco es el cuello.
#   · pico más largo y más abajo, que es el rasgo que separa un pato de un
#     pollito. Es lo primero que se pierde al reducir, así que va sobrado.
#   · la cola era una cuña suelta a la izquierda que a 4 mm parecía suciedad;
#     ahora arranca del cuerpo y sube, como una cola de verdad.
#   · sin ojo: a este tamaño el hueco mediría 0.16 mm y en imprenta se cierra
#     solo. Un ojo que se tapa deja una mancha peor que no tenerlo.
PATITO = ('<svg class="ico-patito" viewBox="0 0 24 24" fill="currentColor" '
          'xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
          # cuerpo, con la cola integrada subiendo por la izquierda
          '<path d="M11.3 20.9c-4.3 0-7.8-2.2-7.8-4.9 0-.5.1-1 .4-1.4L1.1 10.4'
          'c-.3-.5.2-1.1.8-.9l5 1.9c1.2-.8 2.8-1.3 4.4-1.3 4.3 0 7.8 2.2 7.8'
          ' 5s-3.5 4.8-7.8 4.8z"/>'
          # cabeza — apoyada sobre el cuerpo, tocándolo solo en el cuello
          '<circle cx="16.4" cy="7" r="4.3"/>'
          # pico
          '<path d="M20.1 6.9 23.6 8.5 20.1 10.1z"/></svg>')

# 🔤 Llevan nombre accesible (`role="img"` + `aria-label`) y no `aria-hidden`
# como el resto de los íconos. Desde el 2026-08-01 el título de El Duelo dice
# «EL DUELO / 🇨🇴 vs 🇲🇽» **sin las palabras COL y MEX**: las banderas dejaron de
# acompañar al texto y pasaron a SER el texto. Un signo que carga el
# significado no puede esconderse del lector que no lo ve.
BANDERA_CO = ('<svg class="bandera-co" viewBox="0 0 9 6" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Colombia">'
              '<rect width="9" height="3" fill="#FCD116"/>'
              '<rect y="3" width="9" height="1.5" fill="#003893"/>'
              '<rect y="4.5" width="9" height="1.5" fill="#CE1126"/></svg>')

# 🇲🇽 Bandera de México — TERCERA excepción de paleta (dueño, 2026-08-01), solo
# en el título de El Duelo. Está registrada en `style-guide.md` §2.1.
#
# El duelo es Colombia CONTRA México: si un bando lleva su bandera y el otro no,
# no hay duelo. Por eso entra en pareja con la de Colombia y **solo ahí** — no
# marca procedencia de producto como la colombiana, que sí va suelta junto a
# cada licor. En esa reja no debe aparecer nunca: ningún producto es mexicano
# por origen declarado en la carta.
#
# ⚠️ ESTA VA CON ESCUDO, Y POR ESO NO ES SVG DIBUJADO A MANO.
# El primer intento fue una silueta de águila trazada aquí. Se descartó tras
# medirla: a 4 mm leía como una mancha con cuernos, y **sin escudo legible una
# tricolor verde-blanco-rojo es la bandera de Italia** — que fue exactamente lo
# que reportó el dueño al ver el render.
#
# 📌 La fuente es la bandera OFICIAL de Wikimedia Commons
# (`Flag_of_Mexico.svg`, 980×560), rasterizada a 1400×800 px.
#   · **Dominio público**: la ley federal de derecho de autor de México, art. 14
#     frac. VII, excluye escudos, banderas y emblemas de la protección.
#   · Se rasteriza en vez de incrustar el SVG porque el original trae **350
#     paths, ~30 colores y 3 degradados radiales**. Los degradados chocan con el
#     aplanado del PDF (CLAUDE.md: la transparencia viva se resuelve mal en
#     algunos lectores) y a este tamaño ese detalle no se ve: solo estorba.
#   · A 10.5 mm de ancho impreso el PNG da **3387 dpi**, muy por encima de los
#     320 de objetivo. Pasa por el mismo camino a CMYK que las fotos, así que
#     `auditar_resolucion.py` y `preparar_pdf_imprenta.py` ya la controlan.
#
# ⚖️ **Nota legal, distinta del copyright**: el uso de los símbolos patrios sí
# está regulado en México (Ley sobre el Escudo, la Bandera y el Himno). La ley
# pide **reproducción fiel**, así que usar la oficial es el lado seguro — es la
# versión dibujada a mano la que se apartaba de la norma. Registrado en §2.1-ter.
BANDERA_MX = ('<img class="bandera-mx" src="../assets/marca/bandera-mx.png" alt="México">')

# ☠️ Shot cayendo dentro del tarro — ícono del panel "Envenena tu cerveza".
# Dibujado en el trazo del proyecto (stroke 1.7, uniones redondas), como la
# cámara y los íconos de familia: nunca un ícono de librería. Cuenta el
# producto sin leer — un caballito que cae, dos gotas y el tarro con espuma.
SHOT_EN_TARRO = (
    '<svg class="env-ico" viewBox="0 0 32 32" fill="none" stroke="currentColor" '
    'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" '
    'xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
    # caballito de guaro cayendo, boca abajo
    '<path d="M11.2 2.4h8l-1.2 6a1.6 1.6 0 0 1-1.6 1.3h-2.4a1.6 1.6 0 0 1-1.6-1.3Z"/>'
    # el chorro que cae, partido en dos: es lo que da el movimiento
    '<path d="M15.2 11.7v1.6"/><path d="M15.2 14.7v0.9"/>'
    # espuma del tarro (la onda es lo que lo hace tarro y no vaso)
    '<path d="M6.4 17.6c1.1-1.9 2.6-1.9 3.7-.2 1.1 1.7 2.6 1.7 3.7 0 1.1-1.7 2.6-1.7 3.7.2"/>'
    # cuerpo del tarro — SIN arista superior: la recta del borde se sumaba a la
    # onda de espuma y a 9.5 mm el conjunto se leía como una tapa plana.
    '<path d="M6.4 17.6v9.2a2.4 2.4 0 0 0 2.4 2.4h6.3a2.4 2.4 0 0 0 2.4-2.4v-9.2"/>'
    # asa
    '<path d="M17.5 20.2h2.2a2.3 2.3 0 0 1 2.3 2.3v2.1a2.3 2.3 0 0 1-2.3 2.3h-2.2"/>'
    '</svg>')

# 🥃🍾 Caballito y botella del bloque de El Duelo (§6.49.5, rediseñado el
# 2026-08-01). Mismo trazo que SHOT_EN_TARRO y que la cámara —stroke 1.7,
# uniones y remates redondos—: **nunca un ícono de librería** (§2.2).
# El caballito reutiliza a propósito la silueta del que ya cae dentro del tarro
# en «Envenena tu cerveza», dos bloques más arriba de la misma página: el
# cliente ya vio esa forma, así que aquí no estrena signo, reconoce uno.
# 📌 Van a 3-3.4 mm y por eso son de trazo y no de masa: a ese tamaño una
# silueta rellena se cierra, un contorno sigue leyéndose.
SHOT_COPA = (
    '<svg class="cd-ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" '
    'xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
    # cuerpo troncocónico — la conicidad es lo que lo separa de un vaso normal
    '<path d="M6.6 3.5h10.8l-1.5 13.2a2 2 0 0 1-2 1.8h-3.8a2 2 0 0 1-2-1.8Z"/>'
    # base: sin ella el caballito flota y a 3 mm parece un cubo
    '<path d="M9.4 20.5h5.2"/></svg>')

BOTELLA = (
    '<svg class="cd-ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" '
    'xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
    # cuello, hombro y cuerpo de un tirón
    '<path d="M10.2 2.5h3.6v4.1c0 .7.3 1.4.8 1.9l.9 1a3 3 0 0 1 .8 2v8a2 2 0 0 1'
    '-2 2H9.7a2 2 0 0 1-2-2v-8a3 3 0 0 1 .8-2l.9-1c.5-.5.8-1.2.8-1.9Z"/>'
    # la etiqueta: un solo trazo, y es lo que la hace botella de licor y no frasco
    '<path d="M7.7 13.6h8.6"/></svg>')

CAM = ('<svg class="ph-cam" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">'
       '<path d="M4 8 h4 l2 -2.5 h4 l2 2.5 h4 v11 H4 Z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>'
       '<circle cx="12" cy="13.2" r="3.4" stroke="currentColor" stroke-width="1.6"/></svg>')

ICO_PERSONAS = ('<svg class="ico-personas" viewBox="0 0 26 14" fill="currentColor" xmlns="http://www.w3.org/2000/svg">'
                '<circle cx="6" cy="3.8" r="2.7"/><path d="M1 13 C1 9.8 3.2 8.1 6 8.1 s5 1.7 5 4.9 Z"/>'
                '<circle cx="14.8" cy="3.2" r="2.2"/><path d="M11.6 12.8 c0.3-2.7 1.6-4.1 3.2-4.1 2.2 0 3.6 1.4 3.9 4.1 Z"/>'
                '<circle cx="21.6" cy="4.2" r="1.9"/><path d="M18.9 12.9 c0.4-2.1 1.4-3.3 2.7-3.3 1.7 0 2.8 1.2 3.1 3.3 Z"/></svg>')

# Estrellita del bajorrótulo (§6.57): la chispa de cuatro brazos del sistema no
# vale aquí — a 3mm se lee como un "+". Una estrella de cinco puntas sí.


# ---------- hero ----------


# Decoración de marca (propuesta): blobs suaves de fondo + chispas sueltas,
# como los blobs del menú físico — nunca encima del texto ni de la comida.

# 🎨 Los cuatro ornamentos de MARCA los pone el tema, no este archivo.
# El sello llevaba «DE CORAZÓN Y SABOR · PARCEROS ·» escrito dentro del SVG:
# eso no era un icono, era un logotipo. El motor los pide por ROL y no sabe
# qué dibujo son — que es lo que permite que otro cliente ponga otros.
# Lo demás de este archivo SÍ se queda: la bandera de Colombia, el shot en
# tarro o la botella son vocabulario de carta, no marca.
from .. import tema as _tema

CHISPA = _tema.ACTIVO.ornamento("chispa")
CHISPA_MINI = _tema.ACTIVO.ornamento("chispa_mini")
SELLO = _tema.ACTIVO.ornamento("sello")
DECO_MARCA = _tema.ACTIVO.ornamento("deco_marca")
