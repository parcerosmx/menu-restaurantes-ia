"""La clase `Receta`. Vive aparte por un motivo mecánico, no estético.

`hacer.py` carga las recetas del proyecto, y el proyecto necesita esta clase
para declararlas. Con la clase dentro de `hacer.py` había un ciclo:

    comprobar → recetas (del proyecto) → hacer → recetas (a medio inicializar)
                                                  ↑ RECETAS aún no existe

y salía como «⛔ El `recetas.py` del proyecto no exporta `RECETAS`», que
señala al archivo equivocado. Es el mismo caso que `motor/tema_base.py` y se
resuelve igual: la clase en su propio módulo, sin nada que la haga volver.
"""


class Receta:
    """Un entregable y los pasos que lo producen, en su orden.

    `desde_aqui` marca las recetas que NO pertenecen a ningún proyecto. Las
    demás corren desde la raíz del cliente, porque ahí es donde están su carta
    y su `output/`; pero `crear` levanta un proyecto que todavía no existe, y
    correrla desde la raíz de otro hacía que `menu-ia crear --desde brief.json`
    buscara ese JSON en una carpeta que no es donde el usuario lo escribió. El
    archivo estaba delante y el error decía que no existe — en el primer
    comando que teclea alguien que acaba de instalar el motor.
    """

    def __init__(self, nombre, que, pasos, aviso=None, confirmar=False,
                 desde_aqui=False):
        self.nombre, self.que, self.pasos = nombre, que, pasos
        self.aviso, self.confirmar = aviso, confirmar
        self.desde_aqui = desde_aqui
