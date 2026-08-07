# Axxon Sprint0 Suite

Skills de Sprint 0 de Axxon Consulting para proyectos Dynamics 365 / Power Platform.

## Skills

| Skill | Qué hace |
|---|---|
| `d365-requirements-analyst` | Analiza requerimientos desde RFP/notas/transcripciones, cruza contra BPC, Microsoft Learn, licenciamiento, la librería interna de propuestas, y descompone en Historias de Usuario con tareas y criterios de aceptación en Gherkin |
| `bpc-analyser` | Mapea cualquier requerimiento a su posición exacta en el árbol de 7 niveles del Business Process Catalog de Microsoft (marzo 2026) |
| `refinement-prep` | Prepara el brief de una sesión de refinamiento (funcional/técnica/combinada) para una Épica — hipótesis de fit-gap y preguntas puntuales, leyendo el estado real desde Azure DevOps |
| `fdd-builder` | Genera el Documento de Diseño Funcional (FDD) en Word para un GAP específico, a partir de Historias de Usuario ya refinadas — template de marca Axxon bundleado |
| `backlog-refiner` | Reemplaza en Azure DevOps las Stories candidatas de una Épica (de Fase 0) por las Historias reales, con story points confirmados por el equipo y clasificación fit/gap |
| `fit-gap-rollup` | Agrega la clasificación fit/gap de todas las Historias reales (de una Épica o de todo el proyecto) en un documento de trabajo |
| `effort-recalibration` | Compara el peso original de Fase 0 contra la suma real de story points de Fase 1, agregado de todo el proyecto — se corre una vez, al cierre |

`d365-requirements-analyst` usa `bpc-analyser` internamente para el cruce contra el BPC (Paso
3) y el mapeo en la descomposición de Historias (Paso 7). `refinement-prep`, `fit-gap-rollup`,
y `effort-recalibration` leen Azure DevOps (**solo lectura**) vía `ado_client.py` vendorizado
desde `axxon-ado-connector`. `backlog-refiner` es la única skill de este plugin que **escribe**
en Azure DevOps — siempre con `--dry-run` primero y story points confirmados por el equipo,
nunca inventados. `fdd-builder` toma el output de `d365-requirements-analyst` como input
natural. Flujo completo: `refinement-prep` → sesión con humanos → `d365-requirements-analyst`
→ `backlog-refiner` → (`fdd-builder` si el GAP lo amerita) → `fit-gap-rollup` +
`effort-recalibration` al cierre de Fase 1.

## Origen del contenido

Convertido a partir de fuentes reales de Axxon:
- `d365-requirements-analyst`: adaptado de un spec YAML propio (no era formato de Claude Skill
  nativo) a `SKILL.md` real, preservando toda la metodología original (6 pasos, manejo de
  conflictos y gaps, criterios de calidad). El **Paso 7** (descomposición en Historias de
  Usuario) se fusionó desde una skill separada (`analisis-funcional-dynamics365`) que hacía
  exactamente ese trabajo — se unificaron en una sola skill en vez de dos con triggers
  parecidos, para evitar que Cowork activara la que no correspondía.
- `bpc-analyser`: ya venía en formato `SKILL.md` válido. Se corrigió el nombre
  (`bpc-analyzer` → `bpc-analyser`, para consistencia con el resto del proyecto Axxon) y se
  separó el árbol completo del BPC a `references/bpc-tree.md` para no cargarlo completo en
  cada invocación.
- `fdd-builder`: skill ya real de Axxon, con plantilla Word propia (`assets/Plantilla_FDD.docx`)
  y script `python-docx` funcional. La plantilla traía datos de un proyecto real (cliente
  "Chacomer", GAP de integración Asterisk) — se neutralizó a placeholders genéricos
  (`Cliente X`, `[ID]`, `[Nombre del GAP]`, `[Project ID]`, `[Nombre del autor]`) para uso
  general, y se actualizó `schema_name()` para usar el prefijo `axx_` por defecto en vez de
  `new_`.
- `backlog-refiner`, `fit-gap-rollup`, `effort-recalibration`: diseñadas desde cero para
  cerrar el ciclo de recalibración de esfuerzo — encontramos que sin una skill que escriba
  las Historias reales en ADO, no había número de Fase 1 consultable para comparar contra el
  peso de Fase 0. `backlog-seeder` (en `axxon-strategize-suite`) se ajustó de paso para
  guardar ese peso original como tag en la Épica (`fase0-peso-{n}`), sin el cual la
  comparación no tendría línea base.

## Notas

- No incluye `licensing-analyser`, `rfp-manager`, ni `d365crm-resoruces-estimator` — quedan
  fuera de este plugin por decisión explícita (no son parte de Sprint 0 en la metodología de
  Axxon; ver ADR-004 del proyecto Axxon Dataverse Agent).
