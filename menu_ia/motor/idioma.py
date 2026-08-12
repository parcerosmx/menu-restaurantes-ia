"""idioma — la capa que traduce el menú sin duplicarlo.

⚠️ Este módulo NO sale del split de `build_menu.py`: nace con la versión en
   inglés (dueño, 2026-08-02) y no tiene símbolo de origen en el monolito. Por
   eso no aparece en el MANIFIESTO de `herramientas/partir_build_menu.py`.

Por qué una capa y no una carpeta `secciones-en/`
=================================================
La tentación evidente era copiar las 7 hojas a `secciones-en/` y traducirlas
ahí. Sería **exactamente el error que este proyecto ya documenta dos veces**:
`build_habladores.py` no teclea ni un precio porque un fork de la fuente única
deja *dos verdades impresas en la misma mesa*, y §8.1 prohíbe teclear un precio
compartido en los datos de una sección por el mismo motivo.

Un `secciones-en/` sería ese fork, pero peor: no forkea solo los precios —
forkea los precios, las fotos, los gramajes, qué platillo está activo y en qué
orden va la hoja. El día que el dueño suba un precio o dé de baja un platillo,
el menú en español lo recoge y el de inglés no. Y no se nota en el render:
se nota en la mesa, con el turista pidiendo un plato que ya no existe.

Aquí solo viaja **el texto**. Todo lo demás —precio, foto, orden, activo/
inactivo, layout— lo sigue mandando `secciones/` para los dos idiomas.

El invariante que hace esto seguro
==================================
📌 **Con `idioma = "es"`, `t()` devuelve su argumento sin tocarlo.** El HTML
en español tiene que salir **byte a byte idéntico** al de antes de que este
módulo existiera — que es la misma garantía que `verificar_split.py` le exige
al reparto de archivos, y por el mismo motivo: una caja movida en un menú de
imprenta se paga en plancha.

Lo comprueba `herramientas/verificar_traduccion.py --es-intacto`.

Qué se traduce y qué no
=======================
**No se traduce** (decisión del dueño, 2026-08-02): el **nombre propio** de un
platillo. Un nombre propio de plato regional, un apellido de la casa y
*Ajiaco* se imprimen igual en las dos versiones, y la descripción en inglés es
la que explica qué son. Protege la autenticidad, deja al turista pedir en voz
alta lo mismo que lee, y es el mecanismo que §5.1-ter ya usaba para glosar un
colombianismo — solo que ahora la glosa está en inglés.

Se implementa por omisión, no por lista negra: los campos de nombre de platillo
(`n`, `n2`, el `nombre` del hero) sencillamente **no pasan por `t()`**. Así no
hay que mantener un catálogo de excepciones.

⚠️ La carta de BEBIDAS es el caso mixto, y por eso tiene su propia vía (`tn()`,
más abajo): ahí conviven nombres propios que se quedan —*Ron Viejo de Caldas*,
*Refajo*, *Pony Malta*— con líneas que solo PARECEN nombres y son descripciones
—*Cerveza nacional*, *Agua natural*, *Botella de guaro*, *vaso chelado*—. Esas
últimas en una carta en inglés tienen que leerse en inglés, y la primera versión
de este módulo las dejó todas en español porque las trató como nombres.

**Sí se traduce** todo lo demás: ganchos, descripciones, glosas, notas,
rótulos, categorías, el lema del pie — y los **acompañamientos genéricos** de
`ADICIONES`. *Yuca Frita* o *Papas a la Francesa* no son nombres propios: son
la descripción de una guarnición, y en una carta en inglés se leen *Fried yuca*
y *French fries*. La regla del dueño protege el plato colombiano, no la papa.
"""
import importlib
import unicodedata
from html import escape

# ── Estado del proceso ──────────────────────────────────────────────────────
# Es estado global a propósito. La alternativa era pasar el idioma como
# parámetro por las ~40 funciones del motor, y ese cambio tocaría todas las
# firmas del render para servir a una variable que en un proceso dado **no
# cambia nunca**: cada corrida de `build_menu.py` produce un solo idioma.
_ACTIVO = "es"
_CATALOGO = {}
_NOMBRES = {}

# Textos que se pidieron traducir y no estaban en el catálogo. No se resuelve
# aquí: se acumula y lo reporta `verificar_traduccion.py`, que es quien puede
# plantar el build. Un `raise` en mitad del render dejaría el HTML a medias y
# obligaría a arreglar los textos de uno en uno.
FALTAN = {}

# Modo captura: cuando es una lista, `t()` anota TODO texto que se le pide
# traducir, en orden de render. Lo usa `herramientas/extraer_textos.py`.
#
# Se captura desde el render y no leyendo `secciones/*.py` con el AST a
# propósito: el AST ve también lo que está `"activo": False`, lo que vive en
# un comentario y lo que ninguna zona llega a imprimir — y NO ve el orden real
# ni los textos que el propio motor pone (rótulos, «El favorito», el lema del
# pie). El catálogo tiene que ser exactamente lo que se imprime, ni una línea
# más: una entrada de más es una traducción que nadie revisa y que la guarda
# da por buena.
CAPTURA = None


def fijar(codigo):
    """Activa un idioma para el resto del proceso. `es` es el idioma fuente."""
    global _ACTIVO, _CATALOGO, _NOMBRES
    codigo = (codigo or "es").lower()
    if codigo == "es":
        _ACTIVO, _CATALOGO, _NOMBRES = "es", {}, {}
        return
    try:
        mod = importlib.import_module(f"idiomas.{codigo}")
    except ModuleNotFoundError:
        raise SystemExit(
            f"⛔ No hay catálogo de textos para «{codigo}». "
            f"Se esperaba render/idiomas/{codigo}.py")
    # ⚠️ `FALTAN` se vacía SOLO al CAMBIAR de idioma, no en cada llamada.
    #
    # Esto era `FALTAN.clear()` a secas, y dejaba la guarda de traducción
    # **ciega al interior del menú**. La guarda construye dos piezas seguidas
    # en el mismo idioma —interior y tapas— y cada una llama a `fijar()`: la
    # segunda borraba todo lo que faltaba en la primera. Medido con una
    # traducción quitada a mano: `FALTAN` valía **1 tras el interior y 0 tras
    # las tapas**. La guarda decía «todos traducidos» y el texto salía en
    # español dentro de la página inglesa — que es exactamente el fallo que
    # esta guarda existe para impedir, y no se ve en el HTML: se ve en el PNG.
    #
    # El razonamiento ya estaba escrito abajo para `NOMBRES_VISTOS` —un
    # proceso construye varias piezas seguidas— pero no se había aplicado
    # aquí. Cambiar de idioma sí tiene que vaciarlo: lo que falta en inglés no
    # es lo que falta en francés.
    cambio = _ACTIVO != codigo
    _ACTIVO, _CATALOGO = codigo, mod.TEXTOS
    _NOMBRES = getattr(mod, "NOMBRES", {})
    if cambio:
        FALTAN.clear()
    # NOMBRES_VISTOS NO se vacía aquí: es un registro de diagnóstico y un solo
    # proceso puede construir varias piezas seguidas (interior + tapas, como
    # hace la guarda). Vaciarlo en cada `fijar` dejaba el listado final con lo
    # de la última pieza y nada más.


def activo():
    return _ACTIVO


def _norm(s):
    """Clave de búsqueda tolerante a lo que no cambia el texto impreso.

    Existe por una lección que ya costó una ronda en este repo: los textos
    aprobados viajan verbatim desde `estructura-menu.md` y llegan con espacios
    dobles, saltos de línea de continuación y comillas tipográficas según cómo
    se pegaron. Un catálogo con clave exacta se rompe por un espacio que nadie
    ve, y el síntoma —una frase en español suelta en medio de la página en
    inglés— solo aparece al mirar el PNG.

    NO normaliza acentos ni mayúsculas: eso sí distingue textos de verdad.

    ⚠️ Y **no toca los saltos de línea**. El `\\n` de una descripción no es
    espacio en blanco: es el corte entre el GANCHO y el cuerpo, que
    `piezas.cuerpo_html` usa para poner la primera línea en seminegrilla
    (§6.17.7e). Colapsarlo dejaría la clave legible y la traducción muda —
    el inglés saldría en un solo párrafo, sin gancho, en las 30 fichas que lo
    llevan. La primera versión de este módulo lo colapsaba.
    """
    s = unicodedata.normalize("NFC", s)
    return "\n".join(" ".join(linea.split()) for linea in s.split("\n")).strip()


def t(s):
    """Traduce un texto visible del menú. Identidad en español."""
    if not s:
        return s
    if CAPTURA is not None:
        CAPTURA.append(s)
    if _ACTIVO == "es":
        return s
    clave = _norm(s)
    if clave in _CATALOGO:
        return _CATALOGO[clave]
    # Un texto que es solo número, precio o signo no necesita traducción y no
    # se reporta como falta: «190», «(5)», «+90», «·» son iguales en los dos
    # idiomas. Sin esta salida, la guarda ahogaría las faltas de verdad.
    if not any(c.isalpha() for c in clave):
        return s
    FALTAN[clave] = FALTAN.get(clave, 0) + 1
    return s


def tx(s):
    """Traduce **y** escapa. Es la que usa el motor: en un f-string de HTML,
    `escape()` nunca se puede olvidar, así que se ata a la traducción."""
    return escape(t(s))


# ── Nombres: la vía LENIENTE ────────────────────────────────────────────────
# `t()` es estricta —lo que no está en el catálogo se reporta como falta— y eso
# es correcto para el copy: una descripción sin traducir es un error.
#
# Con los NOMBRES no vale: la regla del dueño es que se queden en español, así
# que lo normal es que no estén en el catálogo. Con `t()` habría que escribir
# Decenas de entradas identidad (nombre propio → el mismo) solo para callar
# la guarda, y un catálogo lleno de ruido es un catálogo que nadie revisa.
#
# `tn()` invierte la omisión: **ausente = se queda en español, y no es falta.**
# Solo se cataloga el nombre que SÍ hay que traducir, y ahí la entrada dice por
# sí sola por qué existe.
#
# 📌 Dónde se usa y dónde no. En la **carta de bebidas** y en El Duelo, porque
# ahí conviven nombres propios («Ron Viejo de Caldas», «Refajo») con
# descripciones que solo parecen nombres («Botella de guaro», «Cerveza
# nacional», «Agua natural»). En los **nombres de platillo** NO: ahí la regla
# es absoluta y no hay caso ambiguo que resolver.
#
# ⚠️ Lo que esto acepta a cambio: un producto nuevo con nombre descriptivo se
# imprimirá en español sin que nada se ponga rojo. Por eso
# `verificar_traduccion.py` los LISTA todos al final — no como error, sino para
# que quien revise el menú en inglés los vea de un vistazo.
NOMBRES_VISTOS = {}


def tn(s):
    """Traduce un NOMBRE si el catálogo lo pide; si no, lo deja como está."""
    if _ACTIVO == "es" or not s:
        return s
    clave = _norm(s)
    traducido = _NOMBRES.get(clave)
    NOMBRES_VISTOS[clave] = traducido
    return traducido if traducido is not None else s


def tnx(s):
    """`tn()` + escape."""
    return escape(tn(s))


def ts(s, sep):
    """Traduce una línea compuesta y la parte DESPUÉS, no antes.

    El motor parte varias líneas por un separador —`hero.pre` y la línea de
    personas por «·»— y traducir cada mitad por separado obligaría a catalogar
    fragmentos sueltos como «1–2 personas» fuera de su frase. Se traduce la
    frase entera, que es como se aprueba y como se lee, y se parte después.
    """
    return [x.strip() for x in t(s).split(sep, 1)]
