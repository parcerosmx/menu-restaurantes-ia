# De cero a un PDF de imprenta

Quince minutos, sin conocer el proyecto.

---

## 1 · Instalar

```bash
pip install git+https://github.com/<usuario>/menu-restaurantes-ia
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
export MENU_PROYECTO=$PWD/render MENU_CARTA=carta \
       MENU_TEMA=cantina MENU_FORMATO=a4-hoja

menu-ia menu        # el HTML y sus PNG de revisión
menu-ia imprenta    # el archivo del taller, verificado
```

Los PNG salen en `output/`. Míralos: es lo que se aprueba.

## 3 · Crear el tuyo

```bash
python3 -m menu_ia.crear --desde brief.json --en ~/src/mi-restaurante
```

El `brief.json` mínimo:

```json
{
  "nombre":  "Mi Restaurante",
  "slug":    "mio",
  "formato": "a4-hoja",
  "lema":    "",
  "hojas": [
    {"seccion": "Cocina", "slug": "cocina", "arquetipo": "hoja", "items": [
      {"n": "Un plato", "precio": "120",
       "desc": "El gancho.\nQué trae y cómo está hecho."}
    ]}
  ]
}
```

Deja el esqueleto y te dice qué correr después. El skill `crear-menu` hace la
entrevista si prefieres partir de una foto de tu carta actual.

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
