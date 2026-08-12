---
name: crear-menu
description: Arrancar el menú impreso de un restaurante NUEVO desde cero — crear su proyecto, su identidad y su carta a partir de lo que el dueño ya tenga (una foto de su carta actual, un PDF, una lista suelta). Usa este skill cuando alguien diga que quiere hacerle el menú a un restaurante, que tiene un cliente nuevo, que hay que montar una carta desde cero, o cuando pregunte cómo empezar un proyecto con este motor. NO es para cambiar un menú que ya existe — para eso están agregar-platillo, cambiar-precio y cambiar-foto.
---

# Arrancar el menú de un restaurante nuevo

El objetivo de esta primera sesión **no es un menú terminado**. Es un proyecto
que construye, con la carta real dentro, para poder discutir sobre algo montado
en vez de sobre una idea.

## La regla que manda aquí

🤖 **El dueño no teclea su carta.** Si termina dictando platillo por platillo
lo que hay en una foto, el software falló aunque funcione.

El camino principal es **pedirle el material crudo** —una foto de su carta
actual, el PDF que le hizo el diseñador anterior, el export del POS, una nota
de voz— y extraer de ahí. Tú propones el resultado ya armado; él corrige.

Teclear a mano es la salida secundaria: para lo que no tiene comprobante, o
para arreglar lo que leíste mal.

## Lo que hay que averiguar, y en qué orden

Pregunta **solo lo que no puedas deducir del material**. Y de una en una: una
lista de ocho preguntas de golpe se contesta mal.

### 1 · El material

> «¿Tienes una foto de tu carta actual, un PDF, o un export de tu punto de
> venta? Con eso saco los platillos y los precios y tú los revisas.»

Si no tiene nada, entonces sí: los productos a mano, por familias.

### 2 · El formato — la única pregunta que hay que hacer siempre

No se deduce de una foto, y condiciona todo lo demás.

| Si dice… | Formato |
|---|---|
| «una hoja», «algo sencillo», «para plastificar» | `a4-hoja` |
| «un cuadernillo», «como un librito», «con fotos» | `parceros-cuadernillo` |

`menu-ia crear` los lista con `python3 -m menu_ia.formato`.

⚠️ **La cuenta de páginas es dura.** `a4-hoja` admite 2 páginas de contenido;
un cuadernillo grapado, múltiplos de 4. Si la carta no cabe, el andamio **se
planta y dice cuánto sobra** — no lo apliques a la fuerza, vuelve al dueño.

### 3 · La identidad, con la expectativa bien puesta

> «¿Tienes colores y tipografías de marca, o partimos de algo sobrio?»

📌 **Di claro qué va a salir**: el motor genera una piel de arranque —una tinta
de acento, letra del sistema, sin adornos— que sirve para **ver la carta
montada**, no para imprimir. Diseñar su identidad es el trabajo que viene
después, y es la parte que se cobra.

Si un dueño espera su menú terminado al final de esta sesión, corrige eso
ahora, no cuando vea el PNG.

## Montarlo

Escribe el encargo en un JSON y deja que el andamio haga el resto. **No crees
los archivos a mano**: el generador es determinista y se puede volver a correr;
una carpeta hecha a mano no.

```json
{
  "nombre":  "Panadería El Trigal",
  "slug":    "trigal",
  "formato": "a4-hoja",
  "lema":    "Horneado cada mañana",
  "colores": {"papel": "#FDFBF6", "tinta": "#2B2118", "acento": "#A6641E"},
  "hojas": [
    {"seccion": "Panadería", "slug": "pan", "arquetipo": "hoja", "items": [
      {"g": "De masa madre", "n": "Hogaza de campo", "u": "(800 g)",
       "precio": "95",
       "desc": "Veinticuatro horas de fermentación.\nCorteza gruesa, miga húmeda."},
      {"n": "Baguette", "precio": "45"}
    ]}
  ]
}
```

```bash
python3 -m menu_ia.crear --desde brief.json --en ~/src/<cliente>
```

Las claves de un item: `n` nombre · `precio` **solo dígitos** · `desc` (la
primera línea es el gancho, se imprime distinta) · `u` unidades · `g` el
subgrupo, que abre título.

⚠️ **Precios sin `$`, sin comas y sin decimales.** Y el precio **nunca** se
alinea en columna: la piel de arranque ya lo pone pegado al nombre, y eso no
es gusto — una carta con los precios alineados se lee como un comparador y baja
el ticket.

## Después de crear

```bash
cd ~/src/<cliente>
export MENU_PROYECTO=$PWD/render MENU_CARTA=carta \
       MENU_TEMA=<slug> MENU_FORMATO=<formato>
python3 -m menu_ia.formato --aplicar
python3 -m menu_ia.tema --aplicar
menu-ia menu
```

**Mira los PNG antes de enseñar nada.** Salen en `output/`. Es la primera vez
que existe esa carta montada y es donde se ven los problemas de verdad: una
familia que no cabe, un nombre larguísimo, una sección vacía.

Y fija las huellas solo cuando lo que hay sea correcto:

```bash
menu-ia comprobar --fijar
```

⚠️ `--fijar` firma lo que haya, no lo valida. Si fijas una regresión, la guarda
pasa a proteger el fallo.

## Qué NO prometer

- **No es un archivo de imprenta todavía.** Eso es `menu-ia imprenta`, y no se
  da por bueno hasta abrirlo en Illustrator — la prueba local la pinta otro
  motor, y ese motor ya aprobó una vez un archivo que en el taller salió entero
  en negro.
- **Un formato sin prueba de plancha no se vende como probado.** El cuadernillo
  ha llegado a máquina; la hoja suelta verifica en todo lo medible pero no ha
  pasado por Illustrator.
- **La piel no es su identidad.** Repítelo al entregar los primeros PNG.

## Descripciones

Si el dueño no las tiene, el motor imprime «descripción pendiente» — un
marcador visible, a propósito: **nada se inventa**. Un menú impreso es una
promesa que dura todo el tiraje.

Escribirlas es un encargo aparte y hay un skill para eso.
