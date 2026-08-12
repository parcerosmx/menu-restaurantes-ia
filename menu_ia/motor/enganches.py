"""Lo que el motor necesita de la carta, sin conocerla.

Por qué existe
-------------
El motor importaba contenido del cliente **hacia dentro**:

    motor/zonas.py     from carta.adiciones import adic_linea
    motor/hero.py      from carta.adiciones import adic_linea, adic_lista_html
    motor/precios.py   from carta.bebidas import BEBIDAS_FAMILIAS
                       from secciones import SPREADS

Con un solo restaurante no molesta. Pero significa que **el motor no arranca
sin `carta/`**, y `carta/` es Parceros: sus adiciones, sus familias de bebidas,
su escalera de jarras. Un paquete instalable que exige el contenido de otro
cliente para importarse no es un paquete, es Parceros con otro nombre.

Aquí se invierte: el motor **declara** lo que necesita y la carta lo
**registra** al cargarse. Si nadie lo registra, el motor no revienta — se
comporta como si esa pieza no existiera, que es lo correcto para un
restaurante que no vende adiciones.

📌 Es el mismo trato que `tema.py` da a los ornamentos: pedir por ROL y no
saber qué dibujo hay detrás. Un tema sin sello no pinta sello; una carta sin
adiciones no pinta la línea de adiciones.

⚠️ El registro ocurre al importar la carta, y `build_menu.py` la importa
**antes** de maquetar. Si algún día se maqueta sin pasar por ahí, lo que sale
es una hoja sin adiciones, no un error — y eso sí es peor. Por eso
`faltantes()` existe: para poder preguntarlo.
"""

# rol → función. Vacío es un estado válido.
_ENGANCHES = {}

# Los roles que el motor sabe usar. Están enumerados a propósito: registrar un
# nombre que el motor no consulta es un error silencioso —la carta cree que
# aportó algo y no lo aporta—, así que se rechaza.
ROLES = {
    # (claves, rotulo) → HTML de la línea tenue de adiciones de un subgrupo.
    "adic_linea",
    # (claves) → los <li> del panel de adiciones del hero.
    "adic_lista_html",
    # Los tres puentes de precio entre hojas (§8.1, fuente única). Son
    # LÓGICA DE LA CARTA, no del motor: `precio_jarra_min` sabe que existe un
    # bloque `hero_jarras` con una escalera, y eso es la forma de los datos de
    # Parceros. Otro cliente cruzará otras cosas, o ninguna.
    "precio_bebida", "precio_jarra_min", "precio_postre",
    # () → lista plana de items del menú, para la guarda de datos.
    # Un proyecto con zonas propias —heroes, apuestas, cruces— sabe recorrer
    # su estructura mejor que el motor; si no lo aporta, el motor hace un
    # recorrido genérico de `SPREADS`.
    "items_planos",
}


def registrar(rol, fn):
    if rol not in ROLES:
        raise ValueError(
            f"⛔ «{rol}» no es un enganche que el motor consulte. "
            f"Conocidos: {', '.join(sorted(ROLES))}")
    _ENGANCHES[rol] = fn


def faltantes():
    """Roles que el motor sabe usar y esta carta no aporta. Informativo."""
    return sorted(ROLES - set(_ENGANCHES))


def adic_linea(claves, rotulo="Agrégale más sabor"):
    fn = _ENGANCHES.get("adic_linea")
    return fn(claves, rotulo) if fn else ""


def adic_lista_html(claves):
    fn = _ENGANCHES.get("adic_lista_html")
    return fn(claves) if fn else ""


def items_planos():
    """La lista plana de items, o `None` si la carta no aporta la suya."""
    fn = _ENGANCHES.get("items_planos")
    return fn() if fn else None


def _precio(rol, *a):
    """Un puente de precio. A diferencia de los adornos, si falta **se para**.

    Un ornamento que no existe deja un hueco y se ve. Un PRECIO que no existe
    dejaría la carta sin número, o peor, con el de otro plato — y esto es un
    impreso: la promesa dura todo el tiraje. La hoja que cruza un precio
    declara que ese puente existe; si no está, es un fallo de la carta, no un
    estado válido.
    """
    fn = _ENGANCHES.get(rol)
    if fn is None:
        raise SystemExit(
            f"⛔ La carta usa un cruce de precio («{rol}») que no ha "
            f"registrado.\n   Regístralo con `motor.enganches.registrar()` o "
            f"quita el cruce de la hoja.")
    return fn(*a)


def precio_bebida(nombre):
    return _precio("precio_bebida", nombre)


def precio_jarra_min():
    return _precio("precio_jarra_min")


def precio_postre(nombre):
    return _precio("precio_postre", nombre)
