# Empezar aquí

**Quieres el menú impreso de tu restaurante y acabas de llegar a este repo.**
Esto es lo que hay que hacer, en orden.

> Si lo que quieres es entender o adoptar el motor —maquetar tú, tocar el
> pipeline, mandar a plancha— ese camino es [`empezar.md`](empezar.md): de
> instalar a PDF de imprenta en quince minutos, sin agente.

---

## 1 · Lo que necesitas antes de empezar

**Nada que tengas que preparar.** En serio: la única forma de hacer esto mal es
esperar a tener la carta ordenada, las descripciones escritas y los colores
decididos. Eso no llega nunca, y mientras tanto no hay nada que mirar.

Con esto ya se construye un menú que se puede ver montado:

| | |
|---|---|
| **El nombre del restaurante** | obligatorio; no hay forma de suponerlo |
| **Algo que comer** | obligatorio; aunque sea una lista de nombres sueltos |

Y con esto se construye **más rápido y mejor**, sin teclear:

- 📷 **Una foto de tu carta actual.** El camino principal. De ahí salen los
  platillos, los precios y las familias; tú corriges lo que se leyó mal.
- 📄 El PDF que te hizo el diseñador anterior, o el export de tu punto de venta.
- 🎤 Una nota de voz diciendo qué vendes.

⚠️ **Si terminas dictando platillo por platillo lo que ya está en una foto, algo
se hizo mal.** Manda la foto.

## 2 · Instalar

```bash
git clone https://github.com/parcerosmx/menu-restaurantes-ia
cd menu-restaurantes-ia
pip install -e . && python -m playwright install chromium
```

Chromium no es opcional: **es el motor de maquetación**. Los PNG que apruebas y
el PDF que se manda al taller salen del mismo render, y eso es lo que garantiza
que lo aprobado es lo que se imprime.

⚠️ **Clonar, no solo `pip install`.** El paquete suelto te da el motor; la
entrevista la lleva el skill `crear-menu`, que vive en `.claude/skills/` de este
repo.

## 3 · El prompt

Abre [Claude Code](https://claude.com/claude-code) en esa carpeta y pega el
prompt de [`PROMPT.md`](../PROMPT.md). Ahí está la única copia, y ahí se explica
por qué está escrito así.

## 4 · Qué va a pasar

1. **Te pregunta poco y de una en una.** Lo que pueda leer de tu material, no te
   lo pregunta. La única pregunta que siempre hay que hacer es en qué formato
   quieres la pieza —una hoja, un cuadernillo— porque de una foto no se deduce.
2. **Construye en cuanto alcanza.** No espera a tener todo.
3. **Te enseña PNG.** Es la primera vez que tu carta existe montada, y es donde
   se ven los problemas de verdad: una familia que no cabe, un nombre larguísimo,
   una sección con quince cosas seguidas.
4. **Te dice qué falta**, en tres montones y por orden de lo que aporta.

---

## El suelo mínimo

Esto es un encargo completo y válido:

```json
{"nombre": "Taquería La Esquina",
 "items": [{"n": "Taco de pastor"},
           {"n": "Taco de suadero", "precio": "28"},
           {"n": "Gringa", "precio": "75",
            "desc": "Con queso y piña.\nEn tortilla de harina."}]}
```

```bash
menu-ia crear --desde brief.json --en ~/src/mi-restaurante
```

Lo que no dijiste se resuelve solo, **y se anuncia al crearlo**:

| Lo que falta | Qué pasa |
|---|---|
| `slug` | se deriva del nombre |
| `formato` | se propone el que ese contenido llena exacto |
| secciones | una lista suelta es una sección llamada «Carta» |
| `precio` | se imprime **«precio pendiente»**, con esas palabras |
| `desc` | se imprime **«descripción pendiente»** |
| colores | la paleta neutra de arranque — un gris que se nota |
| lema | ninguno |

📌 **Nada se inventa y nada se calla.** Un menú impreso es una promesa que dura
todo el tiraje: si falta un precio, el motor no se lo imagina ni lo esconde — lo
imprime en palabras, para que sea imposible mandarlo así sin verlo.

⚠️ **El formato es la única cuenta dura.** Una hoja a una cara son 1 página; a
dos caras, 2; un cuadernillo grapado, 14 de contenido. El contenido tiene que
llenar el formato **exacto**, porque una página en blanco dentro de un
cuadernillo es un defecto de imprenta, no un hueco. Si no cuadra, el motor se
planta y dice cuánto sobra o falta — eso lo decide el restaurante, no la
herramienta.

## La escalera: qué gana cada cosa que añadas

En cualquier momento:

```bash
menu-ia pendientes
```

Lee tu carta **real** —no el encargo con el que nació el proyecto— y la ordena
en tres montones. Lo que ya arreglaste deja de salir; lo que creció mientras
tanto aparece solo.

| | |
|---|---|
| ⛔ **Antes de imprimir** | se imprimiría tal cual, con la palabra «pendiente» |
| 📈 **Sube la nota** | hueco medible, con su criterio de la rúbrica y su peso |
| 🙋 **Solo lo sabes tú** | el motor no puede medirlo, y hay que pedírtelo |

Los pesos son los de [`metodologia/rubrica.md`](../metodologia/rubrica.md), que
es donde vive el criterio y la evidencia detrás de cada uno. Lo que más mueve la
aguja, en orden:

1. **Ventas y margen por producto** (A1, 18 % de la nota). El criterio que más
   pesa, y el motor no lo puede saber. Sin esos números no se puntúa: se marca
   *no verificable*, en vez de rellenarlo a ojo.
2. **Descripciones** (B5). Wansink midió **+27 % de venta** con etiqueta
   descriptiva frente al nombre a secas.
3. **Qué quieres vender** (A4). El motor sabe qué hay en tu carta; no sabe cuál
   es tu plato insignia ni cuál te deja margen. Eso ordena el menú entero.
4. **Tu identidad** (C3). La piel que genera el motor es letra del sistema y una
   tinta: sirve para ver la carta montada, no para imprimirla.

## Lo que NO va a pasar en la primera sesión

Decirlo ahora ahorra una decepción cuando llegue el primer PNG:

- **No sale tu identidad.** La piel de arranque es un andamio honesto —sobrio, sin
  ornamentos, a propósito— para que se note qué falta. Diseñar la identidad de un
  restaurante es otro trabajo.
- **No sale un archivo de imprenta.** Eso es `menu-ia imprenta`, y ese archivo no
  se da por bueno hasta abrirlo en Illustrator: la prueba local la pinta otro
  motor, y ese motor ya aprobó una vez un archivo que en el taller salió entero
  en negro. Está en [`imprenta.md`](imprenta.md).
- **No se inventa ni una descripción.** Si no la tienes, se imprime el marcador.

## Después

| Quiero… | Es |
|---|---|
| saber qué le falta a mi menú | `menu-ia pendientes` |
| una nota, con criterio y evidencia | el skill `auditar-menu` |
| entender por qué el motor decide así | [`metodologia/`](../metodologia/) |
| mandar a la imprenta | [`imprenta.md`](imprenta.md) — hay un paso que ninguna herramienta hace por ti |
