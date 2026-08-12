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
    def __init__(self, nombre, que, pasos, aviso=None, confirmar=False):
        self.nombre, self.que, self.pasos = nombre, que, pasos
        self.aviso, self.confirmar = aviso, confirmar
