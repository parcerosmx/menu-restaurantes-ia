---
name: crear-menu
description: Arrancar el menú impreso de un restaurante NUEVO desde cero — crear su proyecto, su identidad y su carta a partir de lo que el dueño ya tenga (una foto de su carta actual, un PDF, una lista suelta). Usa este skill cuando alguien diga que quiere hacerle el menú a un restaurante, que tiene un cliente nuevo, que hay que montar una carta desde cero, o cuando pregunte cómo empezar un proyecto con este motor. NO es para cambiar un menú que ya existe — para eso están agregar-platillo, cambiar-precio y cambiar-foto.
---

# Arrancar el menú de un restaurante nuevo

El objetivo de esta primera sesión **no es un menú terminado**. Es un proyecto
que construye, con la carta real dentro, para poder discutir sobre algo montado
en vez de sobre una idea.

## Las dos reglas que mandan aquí

🤖 **El dueño no teclea su carta.** Si termina dictando platillo por platillo lo
que hay en una foto, el software falló aunque funcione.

⏱️ **No se acumulan preguntas antes de construir.** En cuanto tengas el nombre y
algo que comer, **construye y enseña**. Lo que falte se apunta y se sigue. Un
dueño al que se le pide reunirlo todo antes de ver nada, no ve nada nunca — y lo
que hace avanzar la conversación es el primer PNG, no la pregunta número seis.

## El suelo: con esto ya se construye

| | |
|---|---|
| **El nombre del restaurante** | no hay forma de suponerlo |
| **Algo que comer** | aunque sea una lista de nombres sueltos, sin precios |

Todo lo demás tiene respuesta por omisión y **el motor la anuncia al crear**:
slug derivado del nombre, formato propuesto por lo que ocupa el contenido, una
lista suelta montada como una sección «Carta», paleta neutra, sin lema. Un
precio o una descripción que falten se imprimen con las palabras «precio
pendiente» / «descripción pendiente» — visibles a propósito.

📌 **Nada se inventa.** No escribas descripciones «de relleno» para que se vea
completo: un menú impreso es una promesa que dura todo el tiraje, y el marcador
es lo que impide que salga a plancha sin que nadie lo note.

## Preguntar

De una en una. Una lista de ocho preguntas de golpe se contesta mal, y quien
monta un menú suele estar en su restaurante entre dos servicios.

Y **pregunta solo lo que no puedas deducir del material**.

### 1 · El material — siempre la primera

> «¿Tienes una foto de tu carta actual, un PDF, o un export de tu punto de
> venta? Con eso saco los platillos y los precios, y tú los revisas.»

De una foto salen los nombres, los precios y muchas veces las familias. Si no
tiene nada, entonces sí: los productos a mano, por familias, y **sin exigir
precios** — un nombre solo ya vale para construir.

### 2 · El formato — la única que hay que hacer siempre

No se deduce de una foto y condiciona la cuenta de páginas.

| Si dice… | Formato | Contenido que pide |
|---|---|---|
| «una hoja», «para plastificar», «algo sencillo» | `a4-cara` | 1 página |
| «por los dos lados» | `a4-hoja` | 2 páginas |
| «un cuadernillo», «como un librito», «con fotos» | `cuadernillo-esbelto` | 14 páginas |

Si no lo tiene claro, **no lo bloquees**: omite `formato` en el encargo y el
motor propone el que ese contenido llena exacto, y lo dice. Cambiarlo después es
`MENU_FORMATO` y dos comandos.

⚠️ **La cuenta de páginas es dura**: el contenido tiene que llenar el formato
exacto, porque una página en blanco dentro de un cuadernillo grapado es un
defecto de imprenta. Si no cuadra, el andamio se planta y dice cuánto sobra o
falta — **no lo fuerces y no inventes contenido para rellenar**: eso lo decide el
restaurante.

### 3 · La identidad — con la expectativa bien puesta

> «¿Tienes colores y tipografías de marca, o partimos de algo sobrio?»

📌 **Di claro qué va a salir**: una piel de arranque —una tinta de acento, letra
del sistema, sin adornos— que sirve para **ver la carta montada**, no para
imprimir. Diseñar la identidad es el trabajo que viene después, y es la parte que
se cobra. Si el dueño espera su menú terminado al final de esta sesión, corrige
eso ahora y no cuando vea el PNG.

## Montarlo

Escribe el encargo en un JSON y deja que el andamio haga el resto. **No crees
los archivos a mano**: el generador es determinista y se puede volver a correr;
una carpeta hecha a mano no.

El encargo mínimo, que es el caso normal del primer día:

```json
{"nombre": "Taquería La Esquina",
 "items": [{"n": "Taco de pastor"},
           {"n": "Taco de suadero", "precio": "28"}]}
```

Y el completo, cuando ya hay material que lo llene:

```json
{
  "nombre":  "Panadería El Trigal",
  "formato": "a4-cara",
  "lema":    "Horneado cada mañana",
  "colores": {"papel": "#FDFBF6", "tinta": "#2B2118", "acento": "#A6641E"},
  "hojas": [
    {"seccion": "Panadería", "arquetipo": "hoja", "items": [
      {"g": "De masa madre", "n": "Hogaza de campo", "u": "(800 g)",
       "precio": "95",
       "desc": "Veinticuatro horas de fermentación.\nCorteza gruesa, miga húmeda."},
      {"n": "Baguette", "precio": "45"}
    ]}
  ]
}
```

```bash
menu-ia crear --desde brief.json --en ~/src/<cliente>
```

Las claves de un item: `n` nombre · `precio` **solo dígitos** · `desc` (la
primera línea es el gancho, se imprime distinta) · `u` unidades · `g` el
subgrupo, que abre título · `sin_desc` para el plato que **decidieron** que no
lleva descripción, y así deja de contarse como pendiente.

⚠️ **Precios sin `$`, sin comas y sin decimales.** Y el precio **nunca** se
alinea en columna: la piel de arranque ya lo pone pegado al nombre, y eso no es
gusto — una carta con los precios alineados se lee como un comparador y baja el
ticket.

## Después de crear

```bash
cd ~/src/<cliente>
python3 -m menu_ia.formato --aplicar
python3 -m menu_ia.tema --aplicar
menu-ia menu
```

No hay que exportar nada: `menu-ia crear` deja un `.env` y el motor lo lee solo.

**Mira los PNG antes de enseñar nada.** Salen en `output/`. Es la primera vez que
esa carta existe montada y es donde se ven los problemas de verdad: una familia
que no cabe, un nombre larguísimo, una sección con quince cosas seguidas.

## Cerrar la sesión con lo que falta

```bash
menu-ia pendientes
```

Es el entregable de esta primera sesión, junto con los PNG. Lee la carta real
—no el encargo con el que nació el proyecto— y devuelve tres montones: lo que
impide imprimir, lo que sube la nota (con su criterio de la rúbrica y su peso) y
**lo que el motor no puede saber**.

Ese tercer montón es el que hay que conversar, y encabezarlo siempre lo mismo:

> «Lo que más movería tu menú son tus ventas y tu margen por producto, de los
> últimos 30 días. Es el criterio que más pesa de todos y es el único que no
> puedo sacar de la carta.»

Sin esos números la matriz de ingeniería de menú no se puede hacer, y la
auditoría marca ese criterio como **no verificable** en vez de puntuarlo a ojo.
Decirlo el primer día es lo que hace que el segundo encuentro tenga datos.

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

Si el dueño no las tiene, el motor imprime «descripción pendiente» — un marcador
visible, a propósito: **nada se inventa**.

Vale la pena decirle cuánto valen: Wansink (Cornell) midió **+27 % de venta** con
etiqueta descriptiva frente al nombre a secas. Escribirlas es un encargo aparte y
hay un skill para eso.
