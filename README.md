# Menú para Restaurantes con IA

**Genera el PDF que la imprenta acepta sin devolvértelo.** Un motor de menús
impresos que produce el archivo final desde datos y código: CMYK separado con
perfil, negro de texto a una sola tinta, sangrado y cajas declaradas, marcas de
corte y verificación automática antes de mandar nada.

No es una plantilla. Es lo que quedó después de llevar un menú de 16 páginas
hasta la plancha y aprender, tirada a tirada, qué hace que un archivo se
devuelva.

## Por dónde empiezas

### 🍽️ Quiero el menú de mi restaurante

No hay que preparar nada antes. Clona, instala, y pega el prompt:

```bash
git clone https://github.com/parcerosmx/menu-restaurantes-ia
cd menu-restaurantes-ia
pip install -e . && python -m playwright install chromium
```

> **Copia esto en [Claude Code](https://claude.com/claude-code):**
>
> *Quiero hacer el menú impreso de mi restaurante y este repo es el motor. Lee
> `docs/empezar-aqui.md` y llévame tú: pregúntame de una en una, empieza por lo
> que ya tengo a mano —si te doy una foto de mi carta actual, saca todo de ahí—,
> y en cuanto tengas lo mínimo para construir algo que pueda VER, constrúyelo y
> enséñamelo. Lo que falte, lo apuntas y seguimos.*

Te va a preguntar poco, va a construir en cuanto alcance, y después te va a
decir qué le falta a tu menú para vender más. **El suelo mínimo es el nombre del
restaurante y una lista de platillos** — sin precios y sin descripciones vale: lo
que falta se imprime marcado, con esas palabras, para que sea imposible mandarlo
a la plancha sin verlo.

📖 [**El instructivo completo**](docs/empezar-aqui.md) · [el prompt, entero](PROMPT.md)

### 🛠️ Quiero el motor

```bash
cd ejemplos/cantina-del-puerto
menu-ia menu        # el menú y sus PNG de revisión
menu-ia imprenta    # el archivo del taller, verificado
```

📄 **Sin instalar nada:** [el PDF de imprenta del ejemplo](ejemplos/cantina-del-puerto/muestra/menu-cantina-CMYK-sangrado.pdf)
· [una cara montada](ejemplos/cantina-del-puerto/muestra/menu-doble-pagina-1-comer.png)

📖 [**De cero a un PDF de imprenta**](docs/empezar.md) · [**El ritual de plancha**](docs/imprenta.md)

---

## Por qué esto y no InDesign

Un menú impreso no es un objeto gráfico: es **una promesa que dura todo el
tiraje**. Si un precio está mal, está mal en 2 000 cartas.

De ahí salen las cosas que este motor hace y una plantilla no:

- **Un precio se escribe una vez.** Si un producto aparece en dos páginas, las
  dos leen del mismo sitio. El build **se planta** si el mismo producto queda
  impreso a dos precios distintos.
- **Una foto que no existe para el build.** Chromium no protesta: pinta el
  hueco y sigue. Aquí es un error rojo.
- **Los dpi se miden contra la caja impresa**, descontando lo que el recorte
  se lleva. No contra el tamaño del archivo.
- **Se comprueba que nada se movió entre el HTML y el PDF.** Es un fallo real y
  silencioso: sin `break-inside: avoid` el bloque de texto de una portadilla se
  desplaza 14,82 mm en el PDF y en pantalla no se ve.

## Lo que sabe de imprenta

El pipeline no convierte a CMYK y ya:

- **Separa con perfil incrustado** (`OutputIntent`), fondo y texto con el
  **mismo** perfil — si no, el naranja de una foto y el de un titular dejan de
  ser el mismo naranja.
- **Fuerza el negro y los grises neutros del texto a una sola tinta.** El
  perfil convierte el negro puro en 295 % de tinta y cuatro planchas; en un
  cuerpo de 7 pt eso enseña el desregistro de la máquina como un halo de color
  alrededor de cada letra.
- **Aplana la transparencia** conservando el texto en vector. PDF/X-1a la
  prohíbe, y hay lectores que la resuelven mal — bloques grises donde debería
  haber difuminado.
- **Escribe el JPEG CMYK sin la marca Adobe y sin `/Decode`.** Es la única
  combinación que leen igual todos los motores. Con la marca puesta, MuPDF y
  Illustrator **no pueden acertar a la vez**: uno de los dos pinta un fondo de
  poca tinta como negro a cuatro planchas. Averiguarlo costó una tirada.

> ⚠️ **Un archivo de imprenta no se da por bueno hasta abrirlo en Illustrator.**
> La prueba local la pinta MuPDF, y MuPDF ya aprobó un archivo que en el taller
> salía entero en negro. El motor lo dice en su propia salida.

## Cómo está montado

Cuatro cosas separadas, y cada una se cambia sin tocar las otras:

| | Qué decide | Dónde vive |
|---|---|---|
| **Formato** | Cuánto mide el papel, cuánto sangra, cómo se encuaderna | `formato.py` |
| **Tema** | Paleta, tipografías, ornamentos, lema | tu módulo `temas/` |
| **Piel** | El CSS de identidad | tu `piel-<cliente>.css` |
| **Carta** | Los platillos, los precios, el orden | tu paquete de contenido |

El motor aporta `estructura.css` —la mecánica de página que comparte cualquier
menú— y **no conoce a ningún cliente**: pide los ornamentos por rol y los
cruces de precio por enganche.

### Formatos y arquetipos

```python
formato   cuadernillo grapado (múltiplo de 4)  ·  hoja suelta (1 ó 2 caras)
página    pliego (foto a sangre + listado)     ·  hoja (listado denso, sin fotos)
```

La regla de encuadernación es **dato, no comentario**: un contenido de 14
páginas contra un formato de hoja suelta no compila, y dice por qué.

## La metodología

Un menú no se diseña de memoria. [`metodologia/`](metodologia/) recoge por qué
cada decisión es como es, con la evidencia detrás:

- [**Ingeniería de menú**](metodologia/ingenieria-de-menu.md) — la matriz antes
  que el diseño, dónde mira el ojo (y dónde los expertos no coinciden), el
  precio sin símbolo y sin columna, cuánto describir, cuándo la foto resta.
- [**Rúbrica de auditoría**](metodologia/rubrica.md) — 14 criterios, escala
  0–5, y la regla que la hace honesta: un criterio sin su evidencia se marca
  **no verificable** en vez de puntuarse a ojo.
- [**Descripciones**](metodologia/descripciones.md) — cómo se escribe un
  platillo para que se pida.

El skill `auditar-menu` aplica la rúbrica a un menú montado y devuelve la nota,
**la cobertura** y las tres cosas que arreglar primero.

## Empezar un restaurante nuevo

```bash
menu-ia crear --desde brief.json --en ~/src/mi-cliente
```

**El encargo mínimo es el nombre y algo que comer:**

```json
{"nombre": "Taquería La Esquina", "items": [{"n": "Taco de pastor"}]}
```

Lo demás tiene respuesta por omisión y se anuncia al crearlo: el slug se deriva
del nombre, el formato se propone por lo que ocupa el contenido, una lista suelta
es una sección, y un precio o una descripción que falten **se imprimen con esas
palabras** — visibles a propósito, para que no se manden a la plancha sin verlas.

Deja el esqueleto completo —tokens, tema, piel de arranque, carta, `.env`— y dice
qué correr después. El skill `crear-menu` hace la entrevista: pide una **foto de
la carta actual** en vez de que nadie teclee sus platillos.

```bash
menu-ia pendientes    # qué le falta a este menú, y qué gana cada cosa
```

Lee la carta real —no el encargo con el que nació— y la ordena en tres montones:
lo que impide imprimir, lo que sube la nota (con su criterio de la rúbrica y su
peso) y lo que el motor **no puede saber** y hay que preguntarle al dueño.

⚠️ La piel que genera sirve para **ver la carta montada el primer día**, no
para imprimir. Diseñar la identidad de un restaurante es otro trabajo.

## Ejemplo

`ejemplos/cantina-del-puerto/` es un **proyecto completo** de un restaurante
ficticio: A4, dos caras, sin una sola foto. Tiene su carta, su tema, su piel y
sus tokens — es exactamente la forma que tiene un cliente real.

Llega hasta el PDF de imprenta con la verificación completa en verde, y su
salida está commiteada en [`muestra/`](ejemplos/cantina-del-puerto/muestra/)
para poder mirarla sin instalar nada.

## Lo que este motor NO hace

- **No hay editor visual ni web.** Produce archivos desde código y datos, y eso
  es justo lo que lo hace fiable para imprenta.
- **No diseña por ti.** Un cliente nuevo necesita su piel; eso es un encargo de
  diseño, no un archivo de configuración.
- **No garantiza un formato que no se haya probado en plancha.** Los formatos
  que trae marcados como «sin prueba de plancha» verifican el motor, no el
  taller.

## Estado

En construcción abierta. El cuadernillo grapado está probado hasta la plancha;
la hoja suelta verifica en todo lo medible pero **no ha pasado por Illustrator
todavía**.

## Licencia

MIT. Ver [LICENSE](LICENSE).
