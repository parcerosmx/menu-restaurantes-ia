# El prompt inicial

Clona el repo, entra, y pega esto en
[Claude Code](https://claude.com/claude-code). Es todo lo que hay que teclear.

```bash
git clone https://github.com/parcerosmx/menu-restaurantes-ia
cd menu-restaurantes-ia
pip install -e . && python -m playwright install chromium
```

⚠️ **Clonar, no solo `pip install`.** La entrevista la lleva el skill
`crear-menu`, que vive en `.claude/skills/` de este repo: instalando el paquete
suelto tienes el motor, pero no quien sabe preguntar.

```text
Quiero hacer el menú impreso de mi restaurante y este repo es el motor.

Lee `docs/empezar-aqui.md` y llévame tú. Tres cosas:

1. Pregúntame de una en una, empezando por lo que ya tengo a mano ahora
   mismo — si te doy una foto de mi carta actual, sácalo todo de ahí y no
   me hagas teclear lo que ya está en la foto.
2. En cuanto tengas lo mínimo para construir algo que pueda VER, constrúyelo
   y enséñamelo. No esperes a que esté completo.
3. Lo que falte, lo apuntas y seguimos. Al final me dices qué le falta a mi
   menú para vender más, y cuánto pesa cada cosa.
```

---

## Por qué está escrito así

Cada frase evita un fallo concreto, y los tres son de este proyecto:

**«de una en una»** — una lista de ocho preguntas de golpe se contesta mal.
Quien monta un menú está en su restaurante, entre dos servicios.

**«sácalo de la foto»** — si el dueño termina dictando platillo por platillo lo
que hay en una foto, el software falló aunque funcione. El camino principal es
mandar el material crudo: la foto, el PDF del diseñador anterior, el export del
punto de venta, una nota de voz.

**«no esperes a que esté completo»** — un dueño al que se le pide reunirlo todo
antes de ver nada, no ve nada nunca. El motor construye con un nombre y una
lista de platillos; lo que falta se imprime marcado, en palabras, y se cuenta
con `menu-ia pendientes` cada vez que se corre.

## Si no vas a usar Claude Code

El motor es una herramienta de línea de comandos y funciona sin ningún agente:
[`docs/empezar.md`](docs/empezar.md) es el camino a mano, de instalar a PDF de
imprenta, en quince minutos. Lo que se pierde es justo la parte de la entrevista
— alguien tendrá que escribir el JSON del encargo, y eso lo describe
[`docs/empezar-aqui.md`](docs/empezar-aqui.md) §«el suelo mínimo».

## Este archivo es la única copia del prompt

Si lo cambias, cámbialo aquí. El README y la web enlazan a este archivo en vez
de repetirlo, por la misma razón por la que un precio se escribe una sola vez
en toda la carta: dos copias de un dato son dos datos que se contradicen.
