# El ritual de plancha

Qué se comprueba antes de mandar un archivo, y **qué no puede comprobar
ninguna herramienta**.

---

## Lo que el motor verifica solo

`menu-ia imprenta` se planta si algo de esto no cuadra:

- **Todo en CMYK**, con el perfil incrustado como `OutputIntent`.
- **Las tres cajas declaradas**: `MediaBox`, `BleedBox`, `TrimBox`.
- **Fuentes incrustadas** — todas, sin excepción.
- **Sin transparencia viva**: PDF/X-1a la prohíbe y hay lectores que la
  resuelven mal.
- **Cobertura de tinta** bajo el límite del papel.
- **dpi reales** medidos contra la caja impresa, descontando lo que el recorte
  se lleva.
- **El negro del texto a una sola tinta.**

Si eso pasa, el archivo es técnicamente correcto.

---

## ⚠️ Y aun así no está aprobado

**Un archivo de imprenta no se da por bueno hasta abrirlo en Illustrator.**

No es una precaución teórica. La prueba local (`prueba-imprenta.jpg`) la pinta
MuPDF, y **MuPDF ya aprobó un archivo que en el taller salió entero en negro.**

La causa: el JPEG CMYK admite dos convenciones para los mismos bytes —muestras
derechas o invertidas— y la marca Adobe (APP14) dice cuál. Los lectores no se
ponen de acuerdo sobre si esa marca les incumbe:

| | MuPDF / Quartz | Illustrator / Acrobat |
|---|---|---|
| APP14 + `/Decode` | ✅ correcto | 🔴 **negro** |
| APP14, sin `Decode` | 🔴 negro | ✅ correcto |
| **sin APP14, sin `Decode`** | ✅ | ✅ |

Con la marca puesta **los dos motores no pueden acertar a la vez**. El motor
escribe la tercera combinación y **se planta si las otras vuelven** — pero eso
cubre un fallo conocido, no todos los que existen.

📌 La regla que queda: **abre el PDF en Illustrator o Acrobat antes de
mandarlo.** Mira una página de fondo claro y una de foto saturada.

---

## El perfil lo pone el taller

El motor cae a un perfil genérico del sistema y **avisa en amarillo**. Eso vale
para trabajar; no para tirar.

1. Pregúntale al taller qué perfil usa (FOGRA39 es lo habitual en Europa y
   buena parte de América Latina).
2. Pídele su `.icc` — ya no se descargan de fuente confiable.
3. Déjalo en `render/perfiles/` y vuelve a correr la receta.

---

## Un formato que no ha pasado por máquina no está probado

El motor distingue entre *verifica* y *está probado*, y tú también deberías.

| Formato | Estado |
|---|---|
| `cuadernillo-esbelto` | Llegó a plancha. Probado |
| `a4-hoja` | Verifica en todo lo medible. **Sin prueba de plancha** |

Antes de venderle a alguien un formato que nunca se ha impreso, tira una prueba
de una. Sale barato comparado con un tiraje devuelto.

---

## La lista, antes de mandar

1. `menu-ia comprobar --completo` en verde.
2. `menu-ia imprenta` en verde.
3. El PDF **abierto en Illustrator o Acrobat** — fondo claro y foto saturada.
4. El perfil es el que pidió el taller, no el genérico.
5. Si es un formato sin prueba de plancha, hay una prueba impresa.
6. Los precios revisados por quien puede aprobarlos.

El punto 6 no es de imprenta y es el que más caro sale. Un precio mal está mal
en todo el tiraje, y lo corrige un mesero incómodo en cada mesa.
