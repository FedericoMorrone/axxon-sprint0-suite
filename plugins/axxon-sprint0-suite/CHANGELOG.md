# Changelog — Axxon Sprint0 Suite

## v0.1.0 (2026-08-05)

Primera versión empaquetada como plugin de Claude Cowork.

- `d365-requirements-analyst`: convertido desde spec YAML propio a `SKILL.md` real.
- `bpc-analyser`: ya venía en formato válido; corregido nombre (`bpc-analyzer` → `bpc-analyser`)
  y separado el árbol completo del BPC a `references/bpc-tree.md`.
- Excluidas deliberadamente: `licensing-analyser`, `rfp-manager`, `d365crm-resoruces-estimator`
  (no son Sprint 0 en la metodología de Axxon).

## v0.2.0 (2026-08-07)

- Nueva skill `refinement-prep`: prepara el brief de una sesión de refinamiento (funcional,
  técnica, o combinada) para una Épica, con hipótesis de fit-gap y preguntas puntuales —
  nunca respuestas, nunca afirma cómo trabaja el cliente.
- Vendorizado `ado_client.py` desde `axxon-ado-connector` (4to consumidor) — uso exclusivo de
  solo lectura, nunca escribe en Azure DevOps.
- Nuevo script `fetch_epic_context.py`: trae el estado real de una Épica + sus Stories hijas
  desde Azure DevOps (por si cambiaron desde que `backlog-seeder` las creó en Fase 0).

## v0.3.0 (2026-08-07)

- Nueva skill `fdd-builder` (renombrada desde `armado-de-fdd` para respetar la convención de
  nombres en inglés de todo el ecosistema — ver decisión de naming): genera el Documento de
  Diseño Funcional en Word para un GAP específico, con la plantilla de marca Axxon real.
  Plantilla neutralizada (cliente/GAP/autor de ejemplo reemplazados por placeholders
  genéricos), `schema_name()` actualizado a prefijo `axx_`.
- Fusionada `analisis-funcional-dynamics365` dentro de `d365-requirements-analyst` (Paso 7
  nuevo: descomposición en Historias de Usuario + Tareas + Gherkin AC + consideraciones D365)
  — se descartó mantenerlas separadas por solapamiento de triggers.
- Confirmado: FDD y Blueprint general son documentos independientes, distinto propósito.

## v0.4.0 (2026-08-07)

- Nuevas skills para el ciclo de recalibración de esfuerzo: `backlog-refiner` (escribe
  Historias reales en ADO reemplazando candidatas, con story points confirmados por el
  equipo — nunca inventados), `fit-gap-rollup` (agrega clasificación fit/gap, Markdown),
  `effort-recalibration` (compara peso de Fase 0 vs. real de Fase 1, agregado del proyecto).
- Vendorizado `ado_client.py` en las 3 (5to, 6to, y 7mo consumidor de `axxon-ado-connector`).
- `backlog-seeder` (en `axxon-strategize-suite`) ajustado para guardar el peso original de
  Fase 0 como tag `fase0-peso-{n}` en la Épica — sin esto no había línea base para comparar.
- Todas las skills nuevas probadas con datos simulados (sin acceso real a Azure DevOps desde
  el entorno de desarrollo) — validación de sintaxis, lógica de agregación, y casos límite
  (Épicas sin línea base de Fase 0).

## v0.5.0 (2026-08-07)

- Nueva skill `blueprint-builder`: genera el **Solution Blueprint** (cierre formal de Fase 1)
  como HTML con marca Axxon 2025, estructurado según las 10 áreas oficiales del Solution
  Blueprint Review de Microsoft Success by Design (Program, Application, Data, Integration,
  Test, Business Process, Security, ALM, Environment & Capacity, Intelligence strategy —
  confirmadas contra learn.microsoft.com/dynamics365/guidance/fasttrack/solution-workshops).
- Enfoque mixto: 2 áreas (Business Process, Environment & Capacity) se auto-completan leyendo
  Azure DevOps y `.d365-project.md`; las otras 8 las sintetiza Claude a partir de Kickoff
  Brief, FDDs ya generados, notas y transcripciones.
- Nuevo estado `requiere-intervencion-humana`, distinto del `[Pendiente]` normal de
  `fdd-builder` — señala explícitamente que Fase 1 no debería darse por cerrada sin resolver
  esa área. El documento nunca se genera con un área en blanco sin haber preguntado antes.
- `sprint0-analyst`: handoff a Fase 2 actualizado — el Blueprint ya no es un pendiente, es la
  skill de cierre real.
