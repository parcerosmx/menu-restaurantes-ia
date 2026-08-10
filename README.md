# Menú para Restaurantes con IA

**Genera el PDF que la imprenta acepta sin devolvértelo.** Un motor de menús
impresos que produce el archivo final desde datos y código: CMYK separado con
perfil, negro de texto a una sola tinta, sangrado y cajas declaradas, marcas de
corte y verificación automática antes de mandar nada.

No es una plantilla. Es lo que quedó después de llevar un menú de 16 páginas
hasta la plancha y aprender, tirada a tirada, qué hace que un archivo se
devuelva.

```bash
pip install git+https://github.com/<usuario>/menu-restaurantes-ia
menu-ia menu        # el menú y sus PNG de revisión
menu-ia imprenta    # el archivo del taller, verificado
```

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

## Ejemplo

`ejemplos/cantina_del_puerto/` es un restaurante ficticio: A4, dos caras, sin
una sola foto. Llega hasta el PDF de imprenta con la verificación completa en
verde.

```bash
MENU_CARTA=cantina_del_puerto MENU_FORMATO=a4-hoja MENU_TEMA=cantina \
    menu-ia menu
```

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
