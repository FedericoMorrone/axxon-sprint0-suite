---
name: backlog-refiner
description: >
  Reemplaza en Azure DevOps las Stories candidatas de una Épica (sembradas por
  backlog-seeder en Fase 0) por las Historias de Usuario reales, ya refinadas y con story
  points confirmados por el equipo. Las candidatas quedan en estado Removed (nunca se borran),
  las Historias reales se crean con puntos, clasificación fit/gap, y descripción completa
  (tareas + Gherkin AC + consideraciones D365). Usar cuando el usuario pida confirmar el
  refinamiento de una Épica en Azure DevOps, actualizar el backlog real post-sesión, o
  registrar las Historias definitivas de una Épica ya refinada. No usar para generar el
  contenido de las Historias (eso es `d365-requirements-analyst`) ni para desglosar en tasks
  (eso es `ado-us-planner`, Fase 2). Requiere story points ya definidos por el equipo — nunca
  los inventa.
model: sonnet
---

# Backlog Refiner — Fase 1 · Axxon Dataverse Agent

Cerrás el ciclo de una Épica refinada: tomás las Historias reales que ya generó
`d365-requirements-analyst` (con story points confirmados por el equipo, no inventados) y las
escribís en Azure DevOps, reemplazando las Stories candidatas genéricas que `backlog-seeder`
sembró en Fase 0.

---

## Principio de fondo

**Nunca inventás un story point.** Si el usuario te pasa Historias sin puntos asignados, se
los pedís antes de escribir nada — el número tiene que salir de la discusión real del equipo
en la sesión de refinamiento, no de una heurística. Esto es distinto a `backlog-seeder`
(Fase 0), que sí reparte puntos automáticamente porque en ese momento son solo una referencia
gruesa — acá ya estamos en territorio de compromiso real.

## Input requerido

- ID de la Épica en Azure DevOps.
- Lista de Historias refinadas, cada una con: título, descripción, tareas, criterios de
  aceptación (Gherkin), consideraciones D365, **story points**, y **clasificación fit/gap**
  (`fully-covered` / `partially-covered` / `not-covered`).
- Organización y Project de Azure DevOps.

## Flujo

1. Armá el JSON de Historias a partir del output de `d365-requirements-analyst` — si falta
   algún story point o la clasificación fit/gap, pedíselos al usuario antes de seguir.
2. Corré primero en `--dry-run` — mostrá qué Stories candidatas se van a marcar Removed y qué
   Historias nuevas se van a crear, y pedí confirmación explícita antes de ejecutar en serio
   (es una escritura real, mismo criterio que `backlog-seeder`).
3. Con la confirmación, corré sin `--dry-run`:

```bash
python scripts/refine_epic.py --organization axxon --project ClienteX \
  --epic-id 1234 --historias-json historias.json
```

4. Reportá el resultado: Stories candidatas marcadas Removed (con sus IDs), Historias nuevas
   creadas (con sus IDs y links), y cualquier error parcial — nunca digas "listo" si algo falló.

## Qué pasa con las candidatas viejas

**Nunca se borran** — quedan en estado `Removed` con un comentario explicando que fueron
reemplazadas por Historias reales de Fase 1. Esto preserva el historial completo: cualquiera
puede ver después qué candidata genérica de Fase 0 terminó convirtiéndose en qué Historia real.

## Conexión con las skills de recalibración de esfuerzo

Las Historias que esta skill crea quedan con dos datos clave, consultables después:
- **Story Points reales** (Fase 1) — vía `Microsoft.VSTS.Scheduling.StoryPoints`.
- **Clasificación fit/gap** — vía el tag `fit-gap-{clasificación}`.

Esto es lo que después leen `fit-gap-rollup` (agrega las clasificaciones) y
`effort-recalibration` (compara contra el peso original de Fase 0, que `backlog-seeder` ya
guarda en la Épica como tag `fase0-peso-{n}`). Sin esta skill, esas dos no tienen de dónde leer.

## Restricciones

- Nunca escribís sin `--dry-run` primero y sin confirmación explícita del usuario.
- Nunca inventás story points — es un error de validación explícito, no un default silencioso.
- Nunca borrás las Stories candidatas — siempre `Removed` con comentario, nunca delete real.
- No generás el contenido de las Historias — eso ya viene de `d365-requirements-analyst`;
  esta skill solo lo escribe en ADO.
