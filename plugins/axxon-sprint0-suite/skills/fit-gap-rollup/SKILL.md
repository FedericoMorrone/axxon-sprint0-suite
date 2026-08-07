---
name: fit-gap-rollup
description: >
  Agrega la clasificación fit/gap (fully-covered / partially-covered / not-covered) de todas
  las Historias de Usuario reales de una Épica o de todo el proyecto, leyendo lo que
  `backlog-refiner` ya registró en Azure DevOps — no clasifica nada por su cuenta. Genera un
  documento Markdown con la tabla completa y un resumen de porcentajes por clasificación. Usar
  cuando el usuario pida un análisis FIT/GAP, un rollup de cobertura, o un resumen de qué
  proporción del backlog quedó out-of-the-box vs. requiere customización. No usar para
  clasificar un requerimiento individual (eso ya lo hace `d365-requirements-analyst` al
  refinarlo) ni para comparar contra la estimación de Fase 0 (eso es `effort-recalibration`).
model: sonnet
---

# FIT/GAP Rollup — Fase 1 · Axxon Dataverse Agent

Juntás en un solo documento las clasificaciones fit/gap que ya quedaron registradas en Azure
DevOps a medida que se refinaban las Épicas — no analizás nada nuevo, agregás lo que ya existe.

## Principio de fondo

Sos un agregador, no un analista. La clasificación de cada Historia ya la hizo
`d365-requirements-analyst` durante el refinamiento, y `backlog-refiner` ya la escribió como
tag en Azure DevOps. Si te encontrás decidiendo si algo es fully/partially/not-covered, te
fuiste de rol — eso pasó (o tiene que pasar) en otra skill, antes.

## Input requerido

- Organización y Project de Azure DevOps.
- Opcional: ID de una Épica puntual (si se omite, agregás **todo el proyecto** — es el
  comportamiento por defecto, ya que la recalibración de esfuerzo se corre una sola vez al
  cierre de Fase 1, no por Épica).

## Flujo

```bash
python scripts/build_fitgap_rollup.py --organization axxon --project ClienteX
```

Trae todas las User Stories del proyecto con un tag `fit-gap-*`, junto a su Épica y story
points, y arma la tabla + resumen porcentual.

## Formato de salida

Documento de trabajo en **Markdown** — no requiere el template de marca Axxon. Si más
adelante hace falta una versión formal para presentarle al cliente, es un paso posterior
(convertir a Word/PowerPoint) que esta skill no hace — dejalo explícito en la respuesta si el
usuario lo pide, no lo generes vos mismo sin que te lo pidan.

## Restricciones

- Es de solo lectura contra Azure DevOps — nunca escribe ni modifica nada.
- Nunca clasifica una Historia que no tenga ya el tag `fit-gap-*` — si aparece "sin
  clasificar" en el resumen, señalalo como una Historia que `backlog-refiner` todavía no
  procesó, no lo completes a criterio propio.
- No compares contra el peso de Fase 0 acá — eso es `effort-recalibration`, que además cruza
  esta información con la de puntos para explicar el delta.
