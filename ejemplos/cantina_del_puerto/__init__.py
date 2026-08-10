"""Carta de demostración — «La Cantina del Puerto» (restaurante ficticio).

Prueba de salida de la Fase 3 del roadmap. Existe para responder a una
pregunta concreta: **¿sirve este motor a un restaurante que quiere una hoja y
ya?** Parceros es 16 páginas grapadas con 34 fotos; esto es lo contrario.

    formato    a4-hoja      210 × 297 mm · una hoja · dos caras
    tema       cantina      editorial, monocroma, sin ornamentos
    arquetipo  hoja         listado denso, sin hero, SIN FOTOS

Se monta con:

    MENU_CARTA=demo_cantina MENU_FORMATO=a4-hoja MENU_TEMA=cantina \\
        python3 render/build_menu.py

⚠️ **El restaurante no existe y los precios son inventados.** No es material
de nadie ni referencia de precios de mercado: es un juego de datos con la
forma correcta, para poder ejercitar el motor sin sacar los números reales de
ningún negocio (ver `confidencialidad.md`).

📌 Y prueba una cosa que no se ve en el HTML: **el motor aguanta una carta sin
una sola foto.** Ninguna zona la exige, así que `auditar_resolucion.py` no
tiene nada que medir y los derivados `-card`/`-hero` dejan de hacer falta. El
presupuesto fotográfico —que en Parceros es la decisión cara— aquí es cero.
"""

# Cara A — lo salado. Una sola cara tiene que llevar la carta entera de
# comida, así que los grupos hacen el trabajo que en un pliego hace la
# portadilla: orientar sin gastar espacio.
_CARA_A = {
    "seccion": "Para comer",
    "slug": "comer",
    "arquetipo": "hoja",
    "subtitulo": "Cocina de puerto, de la lonja a la mesa",
    "items": [
        {"g": "Para empezar",
         "n": "Ostras de la bahía", "u": "(6)", "precio": "180",
         "desc": "Se abren al pedido.\nCon limón, cebolla morada y salsa de la casa."},
        {"n": "Ceviche de la lonja", "precio": "195",
         "desc": "Lo que llegó esta mañana.\nPescado blanco, leche de tigre, camote y cancha."},
        {"n": "Pulpo a la brasa", "precio": "240",
         "desc": "Cuarenta minutos de cocción antes de tocar el fuego.\n"
                 "Sobre puré de papa ahumada y aceite de pimentón."},
        {"n": "Croquetas de jaiba", "u": "(4)", "precio": "150",
         "desc": "Crujientes por fuera, cremosas por dentro."},

        {"g": "De la parrilla",
         "n": "Pescado entero al carbón", "u": "(por kilo)", "precio": "420",
         "desc": "Para dos o tres.\nSe sirve con tortillas, salsa verde y limones asados."},
        {"n": "Camarones al ajillo", "precio": "265",
         "desc": "Guajillo, ajo confitado y mantequilla."},
        {"n": "Almeja chocolata", "u": "(media docena)", "precio": "210",
         "desc": "A la parrilla, con mantequilla de hierbas."},
        {"n": "Costilla de res al carbón", "precio": "310",
         "desc": "Ocho horas de horno y un paso por la brasa."},

        {"g": "Arroces y guisos",
         "n": "Arroz a la tumbada", "precio": "280",
         "desc": "El plato que hay que pedir si vienes por primera vez.\n"
                 "Caldo corto, mariscos del día y epazote."},
        {"n": "Arroz negro", "precio": "260",
         "desc": "Tinta de calamar, alioli de la casa."},
        {"n": "Caldo de mariscos", "precio": "190",
         "desc": "El de siempre, el de todos los domingos."},

        {"g": "Para acompañar",
         "n": "Papas al carbón", "precio": "70"},
        {"n": "Ensalada de la huerta", "precio": "85"},
        {"n": "Frijoles puercos", "precio": "65"},
        {"n": "Tortillas hechas a mano", "u": "(4)", "precio": "35"},
    ],
}

# Cara B — la bebida y el postre. En una hoja suelta el reverso es lo que se
# lee mientras se espera: por eso lleva lo que se pide DESPUÉS de sentarse.
_CARA_B = {
    "seccion": "Para beber",
    "slug": "beber",
    "arquetipo": "hoja",
    "items": [
        {"g": "De la casa",
         "n": "Michelada del puerto", "precio": "95",
         "desc": "Con clamato, salsa inglesa y chile en polvo del molcajete."},
        {"n": "Paloma de temporada", "precio": "130",
         "desc": "Toronja de la sierra, tequila blanco y sal de gusano."},
        {"n": "Margarita de tamarindo", "precio": "140"},
        {"n": "Mezcalita de pepino", "precio": "150",
         "desc": "Mezcal espadín, pepino y hoja santa."},

        {"g": "Cerveza",
         "n": "Artesanal de barril", "u": "(473 ml)", "precio": "95"},
        {"n": "Clara u oscura", "u": "(355 ml)", "precio": "60"},
        {"n": "Sin alcohol", "precio": "55"},

        {"g": "Sin alcohol",
         "n": "Agua de temporada", "precio": "50",
         "desc": "Pregunta cuál hay hoy."},
        {"n": "Limonada con hierbabuena", "precio": "55"},
        {"n": "Café de olla", "precio": "45"},

        {"g": "Postres",
         "n": "Flan de coco", "precio": "95",
         "desc": "La receta de la abuela, y no se cambia."},
        {"n": "Nieve de mamey", "precio": "70"},
        {"n": "Plátano al horno", "precio": "85",
         "desc": "Con crema y piloncillo."},
    ],
}

SPREADS = [_CARA_A, _CARA_B]

# Dos caras, en el orden en que se leen. La cuenta contra el formato la hace
# `build_menu.py`: dos hojas × 1 página = 2, que es lo que declara `a4-hoja`.
ORDEN = ["comer", "beber"]

TITULO = {"es": "La Cantina del Puerto — Carta"}
