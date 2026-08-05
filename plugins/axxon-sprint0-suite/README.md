# Axxon Sprint0 Suite

Skills de Sprint 0 de Axxon Consulting para proyectos Dynamics 365 / Power Platform.

## Skills

| Skill | Qué hace |
|---|---|
| `d365-requirements-analyst` | Analiza requerimientos desde RFP/notas/transcripciones, cruza contra BPC, Microsoft Learn, licenciamiento, y la librería interna de propuestas |
| `bpc-analyser` | Mapea cualquier requerimiento a su posición exacta en el árbol de 7 niveles del Business Process Catalog de Microsoft (marzo 2026) |

`d365-requirements-analyst` usa `bpc-analyser` internamente para el paso de cruce contra el
BPC (Paso 3 de su metodología) — al estar en el mismo plugin, ambas skills se complementan sin
configuración adicional.

## Origen del contenido

Convertido a partir de dos fuentes reales de Axxon:
- `d365-requirements-analyst`: adaptado de un spec YAML propio (no era formato de Claude Skill
  nativo) a `SKILL.md` real, preservando toda la metodología (6 pasos, manejo de conflictos y
  gaps, criterios de calidad) sin agregar ni quitar contenido funcional.
- `bpc-analyser`: ya venía en formato `SKILL.md` válido. Se corrigió el nombre
  (`bpc-analyzer` → `bpc-analyser`, para consistencia con el resto del proyecto Axxon) y se
  separó el árbol completo del BPC a `references/bpc-tree.md` para no cargarlo completo en
  cada invocación.

## Notas

- No incluye `licensing-analyser`, `rfp-manager`, ni `d365crm-resoruces-estimator` — quedan
  fuera de este plugin por decisión explícita (no son parte de Sprint 0 en la metodología de
  Axxon; ver ADR-004 del proyecto Axxon Dataverse Agent).
