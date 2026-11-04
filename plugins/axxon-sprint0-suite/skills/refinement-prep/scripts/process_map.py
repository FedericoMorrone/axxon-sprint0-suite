"""
process_map.py — Mapeo del process template de Azure DevOps (Agile, Scrum, Basic, CMMI).

Vendorizado: la fuente de verdad es la sección 9 de
`axxon-dataverse-agent/docs/ado-contract.md`. Si cambia algo, se cambia ahí primero y se
vuelve a copiar este archivo idéntico en cada carpeta `scripts/` que lo usa.

Verificado contra Microsoft Learn (2026-11-04):
- Tipos de requerimiento y estados: "Default processes and process templates".
- Campos de esfuerzo: "Query by numeric fields" (Story Points = Agile, Effort = Scrum,
  Size = CMMI). Basic usa Effort según evidencia en un proyecto real (no documentado en esa
  página) — verificar si un proyecto Basic falla.

Lecturas: usar REQUIREMENT_CATEGORY_WIQL (funciona con cualquier proceso) y read_effort().
Escrituras: necesitan el proceso explícito (--process) para el tipo y el campo de esfuerzo.
"""

from __future__ import annotations

import os

PROCESSES: dict[str, dict] = {
    "agile": {
        "requirement_type": "User Story",
        "effort_field": "Microsoft.VSTS.Scheduling.StoryPoints",
        "removed_state": "Removed",
    },
    "scrum": {
        "requirement_type": "Product Backlog Item",
        "effort_field": "Microsoft.VSTS.Scheduling.Effort",
        "removed_state": "Removed",
    },
    "basic": {
        "requirement_type": "Issue",
        "effort_field": "Microsoft.VSTS.Scheduling.Effort",
        "removed_state": None,  # Basic no tiene Removed (To Do / Doing / Done)
    },
    "cmmi": {
        "requirement_type": "Requirement",
        "effort_field": "Microsoft.VSTS.Scheduling.Size",
        "removed_state": "Closed",  # CMMI no tiene Removed: se cierra
    },
}

# Filtro WIQL de requerimientos que funciona con cualquier proceso.
REQUIREMENT_CATEGORY_WIQL = "[System.WorkItemType] IN GROUP 'Microsoft.RequirementCategory'"

# Para lecturas: el primero con valor es el esfuerzo del requerimiento.
EFFORT_FIELDS = (
    "Microsoft.VSTS.Scheduling.StoryPoints",
    "Microsoft.VSTS.Scheduling.Effort",
    "Microsoft.VSTS.Scheduling.Size",
)

# Tag para candidatas reemplazadas cuando el proceso no tiene un estado "Removed".
REPLACED_TAG = "reemplazada-fase1"


def get_process(name: str) -> dict:
    key = (name or "").strip().lower()
    if key not in PROCESSES:
        raise ValueError(
            f"Proceso '{name}' no soportado. Válidos: {', '.join(sorted(PROCESSES))}. "
            f"Se ve en Azure DevOps → Project settings → Process."
        )
    return PROCESSES[key]


def read_effort(fields: dict):
    """Devuelve el esfuerzo del requerimiento sin importar el proceso (o None)."""
    for f in EFFORT_FIELDS:
        value = fields.get(f)
        if value not in (None, ""):
            return value
    return None


def add_process_argument(parser) -> None:
    """Agrega --process a un argparse.ArgumentParser (default: env ADO_PROCESS)."""
    parser.add_argument(
        "--process",
        choices=sorted(PROCESSES),
        default=(os.environ.get("ADO_PROCESS") or "").lower() or None,
        help="Process template del proyecto ADO (Project settings → Process). "
             "Obligatorio para escribir work items; también se toma de ADO_PROCESS.",
    )
