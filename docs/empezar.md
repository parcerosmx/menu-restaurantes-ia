# De cero a un PDF de imprenta

Quince minutos, sin conocer el proyecto.

---

## 1 · Instalar

```bash
pip install git+https://github.com/parcerosmx/menu-restaurantes-ia
python -m playwright install chromium
```

Chromium no es opcional: **es el motor de maquetación**. Los PNG de revisión y
el PDF de imprenta salen del mismo render, que es lo que garantiza que lo que
apruebas es lo que se imprime.

## 2 · Correr el ejemplo

El repo trae un restaurante ficticio completo — A4, dos caras, sin una sola
foto.

```bash
cd ejemplos/cantina-del-puerto
menu-ia menu        # el HTML y sus PNG de revisión
menu-ia imprenta    # el archivo del taller, verificado
```

Los PNG salen en `output/`. Míralos: es lo que se aprueba.

No hay que exportar nada: las cuatro variables del proyecto viven en su `.env` y
el motor lo lee solo. Lo que ya esté en el entorno manda, así que
`MENU_FORMATO=a4-cuadernillo menu-ia menu` sigue sirviendo para probar otra caja
sin tocar el archivo.

## 3 · Crear el tuyo

```bash
menu-ia crear --desde brief.json --en ~/src/mi-restaurante
```

El `brief.json` mínimo es **de verdad** mínimo:

```json
{"nombre": "Mi Restaurante", "items": [{"n": "Un plato"}]}
```

Lo que no digas se resuelve y **se anuncia**: el slug sale del nombre, el formato
se propone por lo que ocupa el contenido, una lista suelta se monta como una
sección, y lo que falte —precio, descripción— se imprime con esas palabras. El
encargo completo, con secciones, colores y lema, está en el docstring de
`menu_ia/crear.py`.

Deja el esqueleto y te dice qué correr después. El skill `crear-menu` hace la
entrevista si prefieres partir de una foto de tu carta actual, y
[`empezar-aqui.md`](empezar-aqui.md) es ese camino explicado entero.

---

## Las cuatro cosas que se cambian por separado

| | Qué decide | Dónde |
|---|---|---|
| **Formato** | Cuánto mide el papel y cómo se encuaderna | `MENU_FORMATO` |
| **Tema** | Paleta, tipografías, ornamentos, lema | tu `render/temas/` |
| **Piel** | El CSS de identidad | tu `render/piel-<slug>.css` |
| **Carta** | Platillos, precios, orden | tu `render/carta/` |

Tras tocar el formato o el tema:

```bash
python3 -m menu_ia.formato --aplicar
python3 -m menu_ia.tema --aplicar
```

Escriben los tokens en tu `style.css`, entre centinelas. El build **se planta**
si no concuerdan: Chromium maquetaría con una caja y el PDF declararía otra, y
eso solo se ve en la plancha.

## Cuando algo deje de cuadrar

```bash
menu-ia comprobar              # ¿sigue saliendo lo mismo?
menu-ia comprobar --completo   # + la deriva HTML↔PDF (~2 min)
```

Compara cada PNG contra su huella de referencia. La primera vez, **mira los
PNG** y luego fíjalas:

```bash
menu-ia comprobar --fijar
```

⚠️ `--fijar` firma lo que haya, no lo valida. Si fijas una regresión, la guarda
pasa a proteger el fallo.

## Antes de mandar nada al taller

Lee [`imprenta.md`](imprenta.md). Hay un paso que ninguna herramienta puede
hacer por ti.
