"""Arquetipos de página: qué forma tiene una hoja del menú.

Hasta la Fase 3 aquí había **una sola función**, `spread()`, y daba por hecho
la única forma que existía: página izquierda a sangre + página derecha de
listado. Esa suposición no vivía sola — `build_pdf_plano.py` e `imponer_pdf.py`
contaban páginas de dos en dos, y `build_menu.py` calculaba el total como
`len(ACTIVOS) * 2`.

Un restaurante que quiere **una hoja y ya** rompe las cuatro a la vez. Por eso
esto pasa a ser un despachador: cada arquetipo dice cómo se dibuja **y cuántas
páginas ocupa**, y el resto del proyecto pregunta en vez de suponer.

    pliego   dos páginas enfrentadas: foto a sangre + listado.  (Parceros)
    hoja     una cara de listado denso, sin hero.               (hoja suelta)

⚠️ El arquetipo NO decide el tamaño del papel ni la encuadernación —eso es
`formato.py`— ni cómo se ve —eso es `tema.py` y la piel—. Decide la
**estructura** de la página: qué zonas hay y en qué orden.

Para añadir un arquetipo: una función que reciba la hoja y devuelva HTML, y su
entrada en `ARQUETIPOS` con el número de páginas que ocupa.

⚠️ El REPARTO de este archivo lo genera `herramientas/partir_build_menu.py`.
   Si algo está en el módulo equivocado, se ajusta el MANIFIESTO del
   splitter y se vuelve a correr — no se mueve a mano.
   El CONTENIDO (platillos, precios, textos) sí se edita aquí.
"""
from html import escape

from .bloques import apuestas, placa
from .hero import hero, pie
from .idioma import tx
from .iconos import CHISPA, CHISPA_MINI, DECO_MARCA
from .zonas import listado, listado_denso


def _clases(s):
    """Las clases de tema que una hoja pide para su página de listado."""
    cls = " deco-marca" if s.get("deco") else ""
    if s.get("fondo"):
        cls += f' fondo-{s["fondo"]}'
    if s.get("densidad"):
        cls += f' densidad-{s["densidad"]}'
    if s.get("cls"):
        cls += f' {s["cls"]}'
    return cls


def _cabecera(s):
    """Rótulo de sección y bajorrótulo. Igual en todos los arquetipos."""
    sub = (f'<p class="lista-sub">{CHISPA_MINI}{tx(s["subtitulo"])}{CHISPA_MINI}</p>'
           if s.get("subtitulo") else "")
    return (f'<div class="lista-header">{CHISPA}'
            f'<h1 class="badge-seccion">{tx(s["seccion"])}</h1>{CHISPA}</div>{sub}')


# ── Arquetipo «pliego» ──────────────────────────────────────────────────
def pliego(s, i=0):
    """Dos páginas enfrentadas. El de Parceros; no cambia ni un píxel."""
    extra = s.get("extra", "")
    deco_cls = _clases(s)
    deco = DECO_MARCA if s.get("deco") else ""
    # Tres montajes posibles para la página izquierda: placa de color plano
    # (§6.53), página de apuestas (§6.37) o HERO de foto (el caso normal).
    if s.get("placa"):
        izquierda = placa(s["placa"])
    elif s.get("apuestas"):
        izquierda = apuestas(s["apuestas"])
    else:
        izquierda = hero(s["hero"])
    # §6.57: una hoja puede pedir su propia "escena" —capas absolutas que van
    # POR DEBAJO del contenido (fondo, camino, mascotas)—. Hoy solo la infantil.
    escena = s["escena"]() if s.get("escena") else ""
    return f'''
<div class="spread">
{izquierda}
<section class="page lista-page{deco_cls}">
  {deco}
  {escena}
  <div class="page-inner">
    {_cabecera(s)}
    {listado(s["items"])}
    {extra}
    {pie()}
  </div>
</section>
</div>'''


# ── Arquetipo «hoja» ────────────────────────────────────────────────────
def hoja(s, i=0):
    """Una cara de listado denso, sin hero y sin presupuesto de foto.

    Es el arquetipo del restaurante que quiere **una hoja y ya**: más
    productos por página, sin portadilla que se coma media cara.

    📌 «Sin fotos» no es un arquetipo aparte: es este con el presupuesto
    fotográfico en cero. Un item con `foto` se sigue pudiendo pintar; lo que
    cambia es que ninguna zona lo EXIGE, así que las guardas de dpi y los
    derivados `-card` dejan de ser obligatorios (§6.1).

    ⚠️ Las reglas que no se negocian siguen aquí: el precio NO va en columna
    alineada ni con puntos guía, ni siquiera en modo denso. Que quepan más
    productos no autoriza a convertir la carta en una lista de precios — es
    justo lo que la ingeniería de menú dice que baja el ticket.
    """
    return f'''
<div class="spread hoja-suelta">
<section class="page lista-page{_clases(s)}">
  <div class="page-inner">
    {_cabecera(s)}
    {listado_denso(s["items"])}
    {s.get("extra", "")}
    {pie()}
  </div>
</section>
</div>'''


# nombre → (función, páginas que ocupa)
ARQUETIPOS = {
    "pliego": (pliego, 2),
    "hoja": (hoja, 1),
}


def pagina(s, i=0):
    nombre = s.get("arquetipo", "pliego")
    if nombre not in ARQUETIPOS:
        raise SystemExit(
            f"⛔ La hoja «{s.get('slug', '?')}» pide el arquetipo «{nombre}», "
            f"que no existe. Conocidos: {', '.join(ARQUETIPOS)}")
    return ARQUETIPOS[nombre][0](s, i)


def paginas_de(s):
    """Cuántas páginas ocupa esta hoja. Lo usa la cuenta contra el formato."""
    return ARQUETIPOS[s.get("arquetipo", "pliego")][1]


# `spread` era el nombre de esto cuando solo había una forma posible. Se
# conserva porque `partir_build_menu.py` lo lista en su MANIFIESTO.
spread = pliego
