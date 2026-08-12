---
name: auditar-menu
description: Auditar un menú impreso con la rúbrica de 14 criterios y devolver una nota, la cobertura y las tres cosas que hay que arreglar primero. Usa este skill cuando alguien pida evaluar, puntuar, revisar o criticar un menú —el propio o el de otro restaurante—; cuando pregunte si su carta está bien, qué le falta, por qué no vende, o qué arreglaría primero. También al cerrar una ronda de rediseño para medir si mejoró. NO es para producir el menú — para eso están crear-menu y las recetas del motor.
---

# Auditar un menú

La rúbrica completa está en [`metodologia/rubrica.md`](../../../metodologia/rubrica.md);
el porqué de cada criterio, en [`ingenieria-de-menu.md`](../../../metodologia/ingenieria-de-menu.md).
Esto es el procedimiento.

## Antes de puntuar nada: qué evidencia hay

**Pregúntalo primero, no al final.** Determina el techo de toda la auditoría.

> «¿Tienes datos de venta por producto —unidades y margen— de los últimos
> treinta días o más? Sin eso puedo auditar el menú, pero el criterio más
> pesado se queda sin puntuar y te lo voy a decir en el resultado.»

| Evidencia | Qué desbloquea |
|---|---|
| **Ventas por producto + margen** | A1 (18 %), y con él la matriz entera |
| **Solo el menú montado** | Todo lo demás — cobertura máxima 82 % |
| **Alguien leyéndolo** | Los criterios USR, que de otro modo son criterio experto disfrazado |

⚠️ **Con 14 días de ventas se puede separar lo que vende mucho de lo que vende
poco, pero no dos productos parecidos.** Dilo si es el caso; una matriz sobre
ruido decide mal.

## Puntuar

Uno por uno, en orden: A1 → A4, B1 → B5, C1 → C5. **No saltes a lo visual
primero** — es lo más fácil de opinar y contamina el resto.

Cada nota lleva las tres cosas de §«Cómo se habla de la evidencia»:

1. **Qué se observó**, localizable: hoja, zona, producto.
2. **Contra qué se compara**: el ancla de la escala o una regla del sistema.
3. **Qué subiría la nota un peldaño**: la acción concreta.

**El tercer punto es el entregable.** Sin él esto es un boletín de notas.

### Las dos formas de auditar mal

**Rellenar un N/V.** Si el criterio pide OBJ y no hay datos, se marca N/V y
sale del cálculo. Una nota inventada en el criterio del 18 % no es un dato
aproximado: es un dato falso con aspecto de dato.

**Repartir cincos.** 3 es el estándar profesional, no el aprobado raspado. Si
tu auditoría tiene muchos 5, la rúbrica se está aplicando con la mano blanda y
deja de servir para comparar con la siguiente ronda.

## Qué se entrega

```
Nota global    3,2 / 5     ·     Cobertura 82 %  (A1 en N/V: sin ventas)

  A · Estrategia comercial  2,8    B · Decisión  3,6    C · Ejecución  3,4

LO TRES PRIMERO
1 · …  (criterio, qué se observó, qué hacer)
2 · …
3 · …
```

**Tres, no quince.** Una lista de quince hallazgos no se ejecuta; se archiva.
Ordénalos por *peso del criterio × cuánto sube la nota*, no por lo mucho que
te llamó la atención.

📌 **Y di siempre la cobertura junto a la nota.** «3,4 sobre 5» sin decir sobre
qué porcentaje esconde que no se miró lo más pesado.

## Los requisitos del encargo van aparte

Un cliente trae condiciones que no son de la rúbrica: un plato que no se toca,
una promoción que tiene que caber. Se numeran aparte y se comprueban al final,
una por una.

**No se mezclan con los 14 criterios.** Si entran, la rúbrica deja de ser
comparable entre clientes y se pierde la única razón de tenerla.

## Al terminar

Si la auditoría es de un menú que este motor produce, las acciones se ejecutan
con sus recetas y se cierra con el diff de PNG:

```bash
menu-ia comprobar
```

Y si el rediseño se aprobó, se vuelve a fijar la referencia — **mirando los PNG
antes**, porque `--fijar` firma lo que haya.
