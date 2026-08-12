"""La identidad de La Cantina del Puerto (restaurante ficticio).

Editorial y monocroma: papel frío, UNA tinta de acento, serif de sistema y
**cero ornamentos** — el diccionario va vacío a propósito, para comprobar
que el motor aguanta una marca que no adorna.

⚠️ No es una propuesta para nadie. Ver la cabecera de `piel-cantina.css`.
"""
from menu_ia.motor.tema_base import Tema

TEMAS = {
    "cantina": Tema(
        nombre="cantina",
        colores={
            "papel": "#FBFAF7",
            "tinta": "#14110E",
            "acento": "#8C1D18",
            "gris": "#6E6A65",
            "filete": "#D8D4CD",
            "placeholder-foto": "#E4E1DB",
            "placeholder-texto": "#8A857F",
        },
        fuentes={
            "cuerpo": "'Inter', 'Helvetica Neue', Arial, sans-serif",
            "display": "'Playfair Display', Georgia, serif",
            "badge": "'Playfair Display', Georgia, serif",
            "script": "'Playfair Display', Georgia, serif",
        },
        import_fuentes=(
            "https://fonts.googleapis.com/css2"
            "?family=Inter:wght@300;400;600&family=Playfair+Display:"
            "ital,wght@0,400;0,600;1,400&display=swap"),
        css_piel="piel-cantina.css",
        ornamentos={},          # ninguno: esta marca no adorna
        lema="La Cantina del Puerto",
        nota="Editorial y monocroma. Prueba del motor, no un diseño acabado.",
    ),
}
