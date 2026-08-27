#!/usr/bin/env python3
"""Qué le falta a este menú, y qué gana el restaurante arreglando cada cosa.

Por qué existe
--------------
El motor construye con lo mínimo —un nombre y una lista de platillos— y eso es
a propósito: un dueño al que se le pide reunir TODO antes de ver nada, no ve
nada nunca. Pero «se puede construir» no es «está bien», y la distancia entre
las dos cosas no puede vivir en la memoria de quien hizo la entrevista. Se
acaba la sesión y se acaba el recordatorio.

Esto lo deja por escrito y lo vuelve a calcular cada vez que se corre, leyendo
la carta REAL del proyecto —no el encargo con el que nació—. Así el aviso
envejece con el menú: lo que ya se arregló deja de salir, y lo que creció
mientras tanto aparece solo.

⚠️ **Esto no puntúa.** Auditar es otra cosa: pide el menú montado, datos de
venta y criterio experto (`metodologia/rubrica.md`, skill `auditar-menu`).
Aquí solo se cuentan huecos, y únicamente los que el motor puede ver — por eso
el tercer montón existe y dice en voz alta lo que no puede medir. Un informe
que solo enseña lo medible convence de que lo demás no importa.

Los tres montones
-----------------
    ⛔ antes de imprimir   se imprimiría tal cual, con esas palabras
    📈 sube la nota        hueco medible, con su criterio de rúbrica y su peso
    🙋 solo lo sabes tú    el motor no puede medirlo; hay que pedírselo al dueño

Uso
---
    menu-ia pendientes
    menu-ia pendientes --estricto    # sale 1 si queda algo del primer montón
"""
from __future__ import annotations

import argparse
import importlib
import os
import sys

from . import proyecto

# ── Los pesos son los de la rúbrica, no una escala nueva ────────────────
# `metodologia/rubrica.md` es la autoridad. Copiar aquí solo lo que se cita
# —código, nombre y peso— y NO inventar criterios: un informe que puntúa con
# una escala propia no se puede comparar con la auditoría que viene después,
# que es justo para lo que sirve.
CRITERIOS = {
    "A1": ("Rentabilidad real", 18),
    "A4": ("Memorabilidad e insignia", 7),
    "B1": ("Arquitectura de decisión y carga cognitiva", 6),
    "B2": ("Escaneabilidad", 6),
    "B5": ("Claridad y poder de venta del texto", 6),
    "C1": ("Apetitosidad y desempeño fotográfico", 7),
    "C3": ("Identidad de marca", 4),
}

# El acento de la paleta de arranque (`crear.py`). Si sigue puesto, nadie ha
# elegido un color: no es un gris elegido, es el gris de una herramienta.
GRIS_DE_ARRANQUE = "#7A7A7A"

# Lo escribe `crear.py` en la primera línea de la piel, y se borra a mano
# cuando la piel deja de ser un andamio. Un sentinela explícito es más honesto
# que adivinar por el contenido del CSS: quien la diseñó dice cuándo terminó,
# y mientras no lo diga el aviso sigue saliendo.
SENTINELA_PIEL = "piel-de-arranque"

# Cinco a siete por familia; treinta a cuarenta en la carta entera
# (`metodologia/ingenieria-de-menu.md` §4, Iyengar y Lepper). No es una regla
# dura y el informe lo dice: el número importa menos que poder descartar.
MAX_POR_FAMILIA = 7
MAX_EN_LA_CARTA = 40


def _carta():
    nombre = os.environ.get("MENU_CARTA", "secciones")
    try:
        return importlib.import_module(nombre)
    except ModuleNotFoundError as e:
        if e.name != nombre:
            raise
        raise SystemExit(
            f"⛔ No encuentro la carta «{nombre}».\n"
            f"   Buscada en: {proyecto.RAIZ}\n\n"
            f"   · Si tu carta se llama de otro modo:  MENU_CARTA=<paquete>\n"
            f"   · Si aún no tienes proyecto:          menu-ia crear")


def _items(hoja):
    """Los productos de una hoja, sea del arquetipo que sea.

    Los dos arquetipos guardan su listado en `items`; el `pliego` lleva además
    su portadilla en `hero`, que es un producto más —tiene nombre, precio y
    descripción— y se contaría de menos si se leyera solo `items`. El hero
    llama `nombre` a lo que una fila llama `n`, y sus viñetas `bullets` a lo
    que una fila llama `desc`; se normaliza aquí para que el resto del módulo
    no tenga que saberlo.
    """
    fila = list(hoja.get("items", []))
    h = hoja.get("hero")
    if h:
        fila.insert(0, {"n": h.get("nombre", "?"), "precio": h.get("precio"),
                        "desc": "sí" if h.get("bullets") else None,
                        "_hero": True, "foto": h.get("foto")})
    return fila


def _familia_mas_larga(hoja):
    """El subgrupo más largo de una hoja, no la hoja entera.

    `g` abre un subtítulo y todo lo que sigue le pertenece hasta el siguiente.
    Contar la hoja completa denunciaría como saturada una sección de quince
    productos repartidos en cuatro familias de tres, que es justo lo que la
    metodología dice que SÍ decide rápido: agrupar cuenta igual que partir. Un
    aviso así se cobra caro —dice que arregles lo que ya está bien— y a la
    tercera vez nadie vuelve a correr el informe.

    Devuelve `(nombre_del_grupo, cuántos)`; el nombre es `None` para los
    productos que van antes del primer `g`, que no tienen subtítulo.
    """
    grupos, actual = {}, None
    for it in hoja.get("items", []):
        if it.get("g"):
            actual = it["g"]
        grupos[actual] = grupos.get(actual, 0) + 1
    if not grupos:
        return None, 0
    return max(grupos.items(), key=lambda kv: kv[1])


def _sin_descripcion(it):
    """Un producto SIN texto y sin haber decidido que no lo lleva.

    `sin_desc` es una decisión tomada —el nombre ya dice qué es— y no un
    olvido. Contarla como hueco convertiría este informe en uno de esos que
    denuncian lo que alguien ya resolvió, y a los tres avisos falsos nadie lo
    vuelve a correr.
    """
    return not any(it.get(k) for k in ("desc", "seg", "gancho", "sin_desc"))


def revisar():
    """Los tres montones, ya calculados. Devuelve (bloqueos, mejoras, datos)."""
    carta = _carta()
    from . import formato as _fmt
    hojas = {h["slug"]: h for h in carta.SPREADS}
    orden = getattr(carta, "ORDEN", list(hojas))
    activas = [hojas[s] for s in orden if s in hojas]

    productos = [(h, it) for h in activas for it in _items(h)]
    sin_precio = [(h, it) for h, it in productos if not it.get("precio")]
    sin_desc = [(h, it) for h, it in productos if _sin_descripcion(it)]

    bloqueos, mejoras = [], []

    if sin_precio:
        donde = " · ".join(f"{h['seccion']}: {it.get('n', '?')}"
                           for h, it in sin_precio[:4])
        if len(sin_precio) > 4:
            donde += f" · … y {len(sin_precio) - 4} más"
        bloqueos.append((
            f"{len(sin_precio)} producto(s) sin precio",
            f"En la plancha saldrán con las palabras «precio pendiente».\n"
            f"      {donde}"))

    if sin_desc:
        mejoras.append((
            "B5", f"{len(sin_desc)} de {len(productos)} productos sin descripción",
            "Wansink (Cornell) midió +27 % de venta con etiqueta descriptiva\n"
            "      frente al nombre a secas. Si un plato no la necesita, márcalo\n"
            "      con `\"sin_desc\": True` y deja de contarse aquí."))

    for h in activas:
        familia, n = _familia_mas_larga(h)
        if n > MAX_POR_FAMILIA:
            donde = (f"«{h['seccion']}» tiene {n} productos seguidos sin subgrupo"
                     if familia is None else
                     f"«{familia}», dentro de «{h['seccion']}», tiene {n} productos")
            mejoras.append((
                "B1", donde,
                f"Cinco a siete por familia es donde empieza la parálisis\n"
                f"      (Iyengar y Lepper: hasta 10× más compra con menos opciones).\n"
                f"      Partir no es la única salida: abrir subgrupos con `g` cuenta\n"
                f"      igual — decide más rápido una hoja de doce bien agrupada que\n"
                f"      una de siete sin estructura."))

    if len(productos) > MAX_EN_LA_CARTA:
        mejoras.append((
            "B1", f"{len(productos)} productos en toda la carta",
            f"Treinta a cuarenta es donde el lector vuelve a lo conocido —que\n"
            f"      suele ser lo barato y lo que menos deja."))

    # Las portadillas sin foto solo se cuentan en el arquetipo que las pide.
    # Una hoja suelta sin fotos no es un menú incompleto: es el menú que ese
    # restaurante pidió, y avisarle de una carencia que eligió es ruido.
    sin_foto = [h for h in activas
                if h.get("arquetipo") == "pliego" and not h.get("hero", {}).get("foto")]
    if sin_foto:
        mejoras.append((
            "C1", f"{len(sin_foto)} portadilla(s) de pliego sin foto",
            "El arquetipo `pliego` reserva media cara para una foto a sangre;\n"
            "      sin ella se imprime el hueco marcado. Una foto mala resta más\n"
            "      que ninguna: si no hay fotografía, el arquetipo `hoja` es más\n"
            "      honesto que un pliego con placeholders."))

    # ── Identidad ───────────────────────────────────────────────────────
    try:
        from . import tema as _tema
        t = _tema.ACTIVO
        if t.colores.get("acento", "").upper() == GRIS_DE_ARRANQUE:
            mejoras.append((
                "C3", "el color de acento sigue siendo el gris de arranque",
                "Nadie ha elegido un color todavía: ese gris es el de la\n"
                "      herramienta, puesto neutro a propósito para que se note."))
        if not (t.lema or "").strip():
            mejoras.append((
                "C3", "el menú no lleva lema",
                "Una línea en el pie es lo que un cliente repite cuando\n"
                "      recomienda el sitio. Va en `temas/__init__.py`."))
        piel = proyecto.RAIZ / t.css_piel
        if piel.exists() and SENTINELA_PIEL in piel.read_text(encoding="utf-8"):
            mejoras.append((
                "C3", f"`{t.css_piel}` sigue marcada como piel de arranque",
                "Letra del sistema, una tinta y cero ornamentos: sirve para ver\n"
                "      la carta montada, no para imprimirla. Diseñar la identidad es\n"
                "      el trabajo que viene después. Cuando lo esté, borra la\n"
                "      primera línea del archivo y este aviso se apaga."))
    except SystemExit:
        # Sin tema no se puede opinar de identidad, pero el resto del informe
        # es válido y se entrega igual. Plantarse aquí dejaría a un proyecto a
        # medio montar sin ninguna de las dos cosas.
        mejoras.append(("C3", "no hay tema activo que revisar",
                        "MENU_TEMA no resuelve. El resto de este informe sí es válido."))

    datos = [
        ("A1", "ventas y margen por producto, 30 días o más",
         "Es el criterio que más pesa de la rúbrica entera, y sin esos números\n"
         "      no se puntúa: se marca no verificable. Con 14 días se separa lo que\n"
         "      vende mucho de lo que vende poco, pero no dos platos parecidos."),
        ("B2", "alguien que no conozca la carta, leyéndola",
         "Cuánto tarda en decidir y qué recuerda después. Sin eso, lo que se\n"
         "      llama «se entiende bien» es criterio experto disfrazado de dato."),
        ("A4", "qué platos quiere vender el dueño, y cuáles le sobran",
         "El motor sabe qué hay en la carta; no sabe cuál es el insignia ni\n"
         "      cuál deja margen. Eso ordena el menú entero."),
    ]
    return activas, productos, bloqueos, mejoras, datos, _fmt.ACTIVO


def _linea(cod, titulo, detalle):
    nombre, peso = CRITERIOS[cod]
    print(f"   · \033[1m{titulo}\033[0m")
    print(f"      {detalle}")
    print(f"      → {cod} {nombre} · {peso} % de la nota\n")


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--estricto", action="store_true",
                    help="sale con código 1 si queda algo sin lo que no se imprime")
    args = ap.parse_args()

    activas, productos, bloqueos, mejoras, datos, fmt = revisar()

    print(f"\n\033[1m▶ pendientes\033[0m — qué le falta y qué gana cada cosa\n")
    print(f"   {len(productos)} producto(s) · {len(activas)} hoja(s) · "
          f"formato {fmt.nombre}\n")

    if bloqueos:
        print("\033[1m⛔ ANTES DE IMPRIMIR\033[0m — se imprime tal cual, con esas palabras\n")
        for titulo, detalle in bloqueos:
            print(f"   · \033[1m{titulo}\033[0m\n      {detalle}\n")

    if mejoras:
        print("\033[1m📈 SUBE LA NOTA\033[0m — hueco medible, con su criterio de rúbrica\n")
        for cod, titulo, detalle in sorted(
                mejoras, key=lambda m: -CRITERIOS[m[0]][1]):
            _linea(cod, titulo, detalle)

    print("\033[1m🙋 SOLO LO SABES TÚ\033[0m — el motor no puede medirlo\n")
    for cod, titulo, detalle in datos:
        _linea(cod, titulo, detalle)

    if not bloqueos:
        print("✅ Nada impide construir el archivo de imprenta.")
    else:
        print(f"⚠️  {len(bloqueos)} cosa(s) se imprimirían con la palabra «pendiente».")
    print("   Puntuar el menú es otra cosa: skill `auditar-menu`.\n")

    return 1 if (args.estricto and bloqueos) else 0


if __name__ == "__main__":
    sys.exit(main())
