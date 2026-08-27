"""Dónde está el proyecto del cliente. Lo primero que el motor necesita saber.

El problema
-----------
`motor/rutas.py` calculaba la raíz así:

    REND = Path(__file__).resolve().parent.parent

Es decir, **desde su propia ubicación**. Mientras el motor vivía dentro del
repo del cliente eso daba la respuesta correcta por casualidad. Instalado como
paquete apunta a `site-packages/menu_ia/`, donde no hay ningún `style.css`, ni
`piel-<cliente>.css`, ni `assets/`.

Un motor instalable no puede deducir dónde está el cliente mirándose a sí
mismo. Tiene que preguntarlo.

Cómo se resuelve
----------------
Por orden:

1. `MENU_PROYECTO` — la ruta, si está puesta. Es la vía explícita y la que se
   usa en cualquier automatismo.
2. El `.env` del proyecto —el que escribe `menu-ia crear`— buscado en el
   directorio actual y en su padre. Solo rellena lo que el entorno no traiga:
   nunca pisa una variable puesta a mano.
3. `./render` bajo el directorio actual, si existe. Es la convención con la que
   nació esto y la que siguen los proyectos existentes.
4. El directorio actual.

Lo que tiene que haber ahí: el `style.css` del cliente, su `piel-*.css`, y los
paquetes de contenido (`secciones/`, `carta/`, `temas/`). El motor añade esa
carpeta al `sys.path` para poder importarlos por nombre — es lo que permite que
`MENU_CARTA=secciones` funcione sin que el motor sepa qué es «secciones».

⚠️ **`output/` cuelga del PADRE**, no de la raíz. Es la convención que ya
existía —`render/` produce en `../output/`— y cambiarla habría movido de sitio
los PNG y los PDF de un proyecto que ya está en producción.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

PAQUETE = Path(__file__).resolve().parent

# Las únicas claves que se leen de un `.env`. La lista es cerrada a propósito:
# un archivo del proyecto no tiene por qué poder meter cualquier variable en el
# proceso —PATH, PYTHONPATH— solo por estar en la carpeta desde la que se corre.
CLAVES = ("MENU_PROYECTO", "MENU_CARTA", "MENU_TEMA", "MENU_FORMATO")


def _cargar_env():
    """El `.env` del proyecto, si lo hay y si no está ya puesto en el entorno.

    `crear.py` escribe ese archivo desde el primer día y su docstring prometía
    «para no exportarlo a mano» — pero **nadie lo leía**. Quien creaba un
    proyecto y hacía `cd` a él seguía teniendo que exportar cuatro variables, y
    si se le olvidaba una, el motor cargaba la carta por omisión («secciones»)
    y fallaba nombrando un paquete del que ese usuario no ha oído hablar nunca.
    La promesa estaba escrita y el código no la cumplía.

    ⚠️ Lo que ya esté en el entorno MANDA. Lo explícito gana a lo implícito, y
    sobre todo: así `MENU_FORMATO=a4-hoja menu-ia menu` sigue sirviendo para
    probar otro formato sin editar el archivo.
    """
    aqui = Path.cwd().resolve()
    for base in (aqui, aqui.parent):
        f = base / ".env"
        if not f.is_file():
            continue
        for linea in f.read_text(encoding="utf-8").splitlines():
            linea = linea.strip()
            if not linea or linea.startswith("#") or "=" not in linea:
                continue
            k, v = (x.strip() for x in linea.split("=", 1))
            if k not in CLAVES or k in os.environ:
                continue
            # Una ruta relativa se lee desde donde está el `.env`, no desde el
            # directorio actual: el archivo dice dónde vive el proyecto y esa
            # respuesta no puede depender de desde dónde se invoque.
            if k == "MENU_PROYECTO" and not Path(v).is_absolute():
                v = str((base / v).resolve())
            os.environ[k] = v
        return f
    return None


ENV = _cargar_env()


def _resolver():
    env = os.environ.get("MENU_PROYECTO")
    if env:
        r = Path(env).expanduser().resolve()
        if not r.is_dir():
            raise SystemExit(
                f"⛔ MENU_PROYECTO apunta a «{r}», que no es una carpeta.")
        return r
    aqui = Path.cwd().resolve()
    conv = aqui / "render"
    return conv if conv.is_dir() else aqui


RAIZ = _resolver()
SALIDA = RAIZ.parent / "output"

# El contenido del cliente se importa POR NOMBRE (`MENU_CARTA=secciones`), así
# que su carpeta tiene que estar en el path. Va al principio: si el cliente
# tiene un módulo que se llama igual que uno del motor, manda el suyo — es su
# proyecto.
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))


def script(nombre):
    """La ruta de un script, sea del motor o del proyecto.

    Desde que el motor se instala, un nombre como `build_menu.py` **ya no dice
    dónde está el archivo**: unos son del paquete y otros del cliente, y las
    herramientas que los cargaban por ruta los buscaban todos bajo la raíz del
    proyecto. Ahí murieron `verificar_traduccion.py` y `extraer_textos.py`, las
    dos con un `FileNotFoundError` sobre `render/build_menu.py`.

    El motor va primero, igual que en `hacer.py`: así un proyecto no puede
    sombrear sin querer una pieza del pipeline con un archivo suyo del mismo
    nombre.

    ⚠️ Devuelve la RUTA, no el módulo. Quien llama sigue decidiendo cómo
    ejecutarlo — y en el caso de la guarda de traducción eso es crítico:
    necesita una ejecución FRESCA por idioma (`spec_from_file_location` +
    `exec_module`), porque `build_menu.py` fija el idioma y escribe el HTML al
    importarse. Un `import_module` cacheado devolvería el módulo español en la
    segunda llamada y la guarda informaría de haber verificado un inglés que
    nunca construyó — el fallo de §9.6-bis, esta vez en silencio.
    """
    del_motor = PAQUETE / nombre
    if del_motor.exists():
        return del_motor
    del_cliente = RAIZ / nombre
    if del_cliente.exists():
        return del_cliente
    raise SystemExit(
        f"⛔ No encuentro el script «{nombre}».\n"
        f"   Buscado en el motor ({PAQUETE}) y en el proyecto ({RAIZ}).")


def modulo_fresco(nombre, etiqueta):
    """`(ruta, nombre_de_módulo)` para ejecutar un script desde cero.

    El nombre no es cosmético. Un script del MOTOR usa imports relativos
    (`from . import proyecto`), y ejecutarlo con un nombre suelto lo deja sin
    paquete padre: `ImportError: attempted relative import with no known parent
    package`. Nombrándolo **dentro** del paquete —`menu_ia._bm_en`— Python le
    da `__package__ = "menu_ia"` y los relativos resuelven.

    Un script del PROYECTO usa imports absolutos y no necesita padre, así que
    va con nombre suelto.

    El sufijo por idioma es lo que garantiza la ejecución fresca: dos nombres
    distintos, dos entradas distintas en `sys.modules`, dos ejecuciones reales.
    """
    ruta = script(nombre)
    if ruta.is_relative_to(PAQUETE):
        return ruta, f"{__package__}._{etiqueta}"
    return ruta, f"_{etiqueta}"


def css(nombre):
    """Una hoja de estilo. Se busca en el cliente y, si no está, en el motor.

    `estructura.css` la trae el paquete —es mecánica de página, la comparte
    cualquier menú—; `piel-<cliente>.css` y `style.css` son del cliente. Buscar
    primero en el cliente permite además que alguien sustituya la estructura si
    de verdad la necesita distinta, sin bifurcar el motor.
    """
    del_cliente = RAIZ / nombre
    if del_cliente.exists():
        return del_cliente
    del_motor = PAQUETE / nombre
    if del_motor.exists():
        return del_motor
    raise SystemExit(
        f"⛔ No encuentro «{nombre}».\n"
        f"   Buscado en el proyecto ({RAIZ}) y en el motor ({PAQUETE}).")
