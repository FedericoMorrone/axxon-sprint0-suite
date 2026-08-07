---
name: effort-recalibration
description: >
  Compara el peso estimado en Fase 0 (Kickoff Brief, a nivel de proceso BPC macro) contra la
  suma real de story points de Fase 1 (Historias de Usuario ya refinadas, escritas por
  backlog-refiner), agregado de todo el proyecto. Reporta el delta total y por Épica, y marca
  las Épicas sin línea base de Fase 0. Usar cuando el usuario pida recalibrar el esfuerzo,
  comparar la estimación inicial contra la real, o entender cuánto se desvió el tamaño del
  proyecto después del refinamiento. Se corre una sola vez, al cierre de Fase 1 — no por
  Épica individual. No usar para clasificar cobertura fit/gap (eso es `fit-gap-rollup`, cuyo
  resultado conviene cruzar con este delta antes de comunicarlo al cliente).
model: sonnet
---

# Effort Recalibration — Fase 1 · Axxon Dataverse Agent

Respondés una pregunta concreta al cierre de Sprint 0: **¿cuánto se movió la estimación desde
que se aprobó la propuesta hasta que el equipo terminó de refinar el backlog?**

## Principio de fondo

Es un reporte agregado de **todo el proyecto**, no por Épica — se corre una vez, al cierre de
Fase 1, cuando todas las Épicas relevantes ya pasaron por `backlog-refiner`. Si se corre
antes, con Épicas todavía sin refinar, el número va a estar incompleto — señalalo
explícitamente si detectás Épicas sin Historias reales todavía.

## De dónde salen los dos números

- **Fase 0:** tag `fase0-peso-{n}` que `backlog-seeder` escribe en cada Épica al crearla.
- **Fase 1:** suma de `Story Points` de las Historias reales (identificables por su tag
  `fit-gap-*`, que solo `backlog-refiner` escribe) vinculadas a esa Épica.

No calculás nada nuevo — solo leés ambos números de Azure DevOps y los comparás.

## Input requerido

- Organización y Project de Azure DevOps. Nada más — es siempre agregado del proyecto entero.

## Flujo

```bash
python scripts/build_recalibration.py --organization axxon --project ClienteX
```

## Formato de salida

Markdown: tabla por Épica (peso Fase 0, total Fase 1, delta absoluto y porcentual), totales
del proyecto, y una sección aparte para Épicas sin línea base de Fase 0 (no entran en el
total — hay que decirlo, no ocultarlo).

## Cómo presentar el resultado

No entregues el número solo. Un delta grande sin contexto genera alarma o falsa tranquilidad
según el signo. Sugerí siempre cruzarlo con `fit-gap-rollup` — las Épicas con más Historias
`not-covered`/`partially-covered` son las que más probablemente explican el desvío.

## Restricciones

- Es de solo lectura contra Azure DevOps — nunca escribe ni modifica nada.
- Nunca inventás un peso de Fase 0 para una Épica que no lo tiene — la marcás explícitamente
  como "sin línea base" y la excluís del total, no la asumís en cero ni la omitís en silencio.
- No es una skill de fase-por-fase — si el usuario pide el delta de una sola Épica puntual
  antes de que termine Fase 1, aclarale que esta skill está pensada para el cierre agregado, y
  ofrecé calcularlo igual si insiste, dejando claro que es una lectura parcial.
