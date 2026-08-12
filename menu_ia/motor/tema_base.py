"""La CLASE `Tema`. Vive aparte por un motivo mecánico, no estético.

`tema.py` carga los temas del cliente, y el cliente necesita la clase para
declararlos. Si la clase viviera en `tema.py` habría un ciclo — y uno que
solo aparece al correr `tema.py` COMO SCRIPT, porque entonces su módulo se
llama `__main__` y el `from tema import Tema` del cliente vuelve a ejecutar
el archivo entero. Con la clase aparte no hay ciclo posible.
"""

INI = "  /* ⇩⇩ TEMA GENERADO POR render/tema.py — no editar a mano ⇩⇩ */"
FIN = "  /* ⇧⇧ fin del tema generado ⇧⇧ */"


class Tema:
    """Los valores de una identidad visual.

    `colores` y `fuentes` son diccionarios `token → valor`. El token es el
    nombre sin `--`, y sale tal cual al CSS. Los nombres son **roles**, no
    descripciones: `--naranja-precio` existe porque el precio es un trabajo
    distinto de la voz manuscrita, aunque el color se parezca (§C2: un color no
    hace dos cosas).
    """

    def __init__(self, nombre, colores, fuentes, import_fuentes="",
                 css_piel="", ornamentos=None, lema="",
                 nota=""):
        self.nombre = nombre
        self.colores = dict(colores)
        self.fuentes = dict(fuentes)
        self.import_fuentes = import_fuentes
        # La capa visual del CSS. `estructura.css` la pone el motor; esta la
        # pone el cliente. Ver `herramientas/partir_css.py`.
        # ⚠️ Sin valor por omisión. Ponía `piel-parceros.css`, así que un
        # tema que olvidara declararla heredaba la piel de otro cliente —
        # y el fallo aparece como «no encuentro piel-parceros.css» en un
        # proyecto que nunca oyó hablar de Parceros.
        if not css_piel:
            raise ValueError(
                f"⛔ El tema «{nombre}» no declara `css_piel`. "
                f"Se esperaba algo como `piel-{nombre}.css`.")
        self.css_piel = css_piel
        # 🎨 Los ornamentos de marca, por ROL. El motor pide «la chispa que va
        # en el rótulo de sección» y no sabe qué dibujo es — que es lo que
        # permite que otro cliente ponga otro. Estaban dentro de
        # `motor/iconos.py`, y el sello llevaba «DE CORAZÓN Y SABOR · PARCEROS»
        # escrito en el SVG: eso no es un icono, es un logotipo.
        # ⚠️ Los PICTOGRAMAS de contenido —la bandera de Colombia, el shot en
        # tarro, la botella— NO están aquí: son vocabulario de carta, no marca,
        # y cualquier restaurante que venda un trago los necesita igual.
        self.ornamentos = dict(ornamentos or {})
        # El lema que va al pie de cada hoja. Vacío = sin pie.
        self.lema = lema
        self.nota = nota

    def ornamento(self, rol):
        """El dibujo de ese rol, o cadena vacía si el tema no lo usa.

        Devolver vacío es una respuesta válida: una marca puede no tener sello
        ni decoración de fondo, y el motor tiene que aguantarlo sin un hueco.
        """
        return self.ornamentos.get(rol, "")

    def bloque_css(self):
        lineas = [INI, f"  /* Tema «{self.nombre}».",
                  "     El dato vive en render/tema.py y se aplica con",
                  "     `python3 render/tema.py --aplicar`. */"]
        for k, v in self.colores.items():
            lineas.append(f"  --{k}: {v};")
        lineas.append("")
        for k, v in self.fuentes.items():
            lineas.append(f"  --font-{k}: {v};")
        lineas.append(FIN)
        return "\n".join(lineas)

    def __str__(self):
        out = [f"{self.nombre}", "  colores:"]
        out += [f"    --{k:<18} {v}" for k, v in self.colores.items()]
        out.append("  tipografías:")
        out += [f"    --font-{k:<13} {v}" for k, v in self.fuentes.items()]
        if self.nota:
            out.append(f"  {self.nota}")
        return "\n".join(out)


