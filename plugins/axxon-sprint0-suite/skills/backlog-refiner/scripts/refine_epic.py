"""
refine_epic.py — Reemplaza las Stories candidatas de una Épica (sembradas por backlog-seeder
en Fase 0) por las Historias de Usuario reales, ya refinadas (output de
d365-requirements-analyst en Fase 1).

Las candidatas NO se borran — quedan en estado "Removed" con un comentario explicando por
qué, para no perder el historial. Las Historias reales se crean como nuevas User Stories,
enlazadas a la misma Épica, con:
  - Story Points (dados por el usuario/equipo — esta skill nunca inventa un número)
  - Tag de clasificación fit/gap (fully-covered / partially-covered / not-covered)
  - Descripción completa: historia + tareas + criterios de aceptación Gherkin + consideraciones D365

Uso:
    python refine_epic.py --organization axxon --project ClienteX --process agile \
        --epic-id 1234 --historias-json historias.json --dry-run

`--process` (agile | scrum | basic | cmmi, o env ADO_PROCESS) es obligatorio: define el tipo
de requerimiento a crear, el campo de esfuerzo (Story Points / Effort / Size) y cómo se
retiran las candidatas (Removed en Agile/Scrum; Closed en CMMI; en Basic, sin estado
equivalente, quedan en su estado con el tag "reemplazada-fase1"). Ver process_map.py.

Solo se retiran como candidatas los hijos de la Épica SIN tag "fit-gap-*" ni
"reemplazada-fase1" y no cerrados — así correrlo dos veces no retira requerimientos reales.

`historias.json`:
[
  {
    "titulo": "Registrar una nueva póliza",
    "descripcion": "Como broker, quiero registrar una nueva póliza para...",
    "tareas": ["Definir modelo de datos", "Configurar formulario", "Probar alta"],
    "criterios_aceptacion": [
      "GIVEN un cliente existente WHEN el broker completa el alta THEN la póliza queda creada"
    ],
    "consideraciones_d365": "Entidad axx_poliza (nueva), lookup a Contact.",
    "story_points": 5,
    "fit_gap": "partially-covered",
    "procode_candidato": true,   # opcional — hipótesis: probablemente requiere pro-code
    "us_tecnica": false          # opcional — historia técnica pura (excepción)
  }
]
(En el JSON real, sin los comentarios `#`.)
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from ado_client import AdoClient, AdoError
from process_map import REPLACED_TAG, add_process_argument, get_process

CHILD_LINK_TYPE = "System.LinkTypes.Hierarchy-Forward"
VALID_FIT_GAP = {"fully-covered", "partially-covered", "not-covered"}
REMOVED_COMMENT = (
    "Reemplazada en Fase 1 por requerimientos reales, refinados con el cliente. "
    "Esta candidata era una aproximación genérica de Fase 0 (ver Kickoff Brief) — "
    "se retira en vez de borrarse, para conservar el historial."
)
CLOSED_STATES = {"Removed", "Closed", "Done"}


def extract_child_ids(epic_relations: list[dict]) -> list[int]:
    ids = []
    for rel in epic_relations:
        if rel.get("rel") == CHILD_LINK_TYPE:
            url = rel.get("url", "")
            tail = url.rstrip("/").rsplit("/", 1)[-1]
            if tail.isdigit():
                ids.append(int(tail))
    return ids


def build_story_description(historia: dict) -> str:
    tareas = "\n".join(f"- {t}" for t in historia.get("tareas", []))
    criterios = "\n".join(f"- {c}" for c in historia.get("criterios_aceptacion", []))
    return (
        f"<p><b>Descripción:</b> {historia['descripcion']}</p>"
        f"<p><b>Tareas:</b></p><pre>{tareas}</pre>"
        f"<p><b>Criterios de Aceptación:</b></p><pre>{criterios}</pre>"
        f"<p><b>Consideraciones D365:</b> {historia.get('consideraciones_d365', '')}</p>"
        f"<p><i>Generada en Fase 1 por d365-requirements-analyst, refinada con el cliente."
        f" Reemplaza una Story candidata de Fase 0.</i></p>"
    )


def validate_historias(historias: list[dict]) -> list[str]:
    """Validación previa — nunca escribir con datos incompletos o fit_gap inválido."""
    errors = []
    for i, h in enumerate(historias):
        if not h.get("titulo"):
            errors.append(f"Historia #{i}: falta 'titulo'")
        if not h.get("descripcion"):
            errors.append(f"Historia #{i}: falta 'descripcion'")
        if "story_points" not in h or not isinstance(h["story_points"], (int, float)):
            errors.append(f"Historia #{i} ({h.get('titulo', '?')}): falta 'story_points' numérico — "
                           f"esta skill NUNCA inventa un número, tiene que venir del equipo")
        fit_gap = h.get("fit_gap")
        if fit_gap not in VALID_FIT_GAP:
            errors.append(f"Historia #{i} ({h.get('titulo', '?')}): 'fit_gap' inválido o ausente "
                           f"(debe ser uno de {sorted(VALID_FIT_GAP)})")
        for flag in ("procode_candidato", "us_tecnica"):
            if flag in h and not isinstance(h[flag], bool):
                errors.append(f"Historia #{i} ({h.get('titulo', '?')}): '{flag}' tiene que ser true/false")
    return errors


def build_tags(historia: dict) -> str:
    """Tags del contrato ADO (axxon-dataverse-agent/docs/ado-contract.md §3)."""
    tags = [f"fit-gap-{historia['fit_gap']}"]
    if historia.get("procode_candidato"):
        tags.append("procode-candidato")  # hipótesis de Fase 1, no una decisión
    if historia.get("us_tecnica"):
        tags.append("us-tecnica")
    return "; ".join(tags)


def is_candidate(item) -> bool:
    """Candidata de Fase 0 = hijo sin clasificación fit-gap, no retirado y no cerrado."""
    tags = item.fields.get("System.Tags", "") or ""
    state = item.fields.get("System.State", "")
    return "fit-gap-" not in tags and REPLACED_TAG not in tags and state not in CLOSED_STATES


def retire_candidate(client: AdoClient, item, process: dict) -> None:
    """Retira una candidata según el proceso — nunca la borra."""
    if process["removed_state"]:
        client.update_work_item(item.id, {
            "State": process["removed_state"],
            "System.History": REMOVED_COMMENT,
        })
    else:  # Basic: no hay estado equivalente a Removed — se marca con tag y comentario
        tags = item.fields.get("System.Tags", "") or ""
        new_tags = f"{tags}; {REPLACED_TAG}" if tags else REPLACED_TAG
        client.update_work_item(item.id, {
            "System.Tags": new_tags,
            "System.History": REMOVED_COMMENT,
        })


def refine_epic(client: AdoClient, epic_id: int, historias: list[dict], dry_run: bool,
                process: dict) -> dict:
    epic = client.get_work_item(epic_id, expand="relations")
    children = [client.get_work_item(cid) for cid in extract_child_ids(epic.relations)]
    candidates = [c for c in children if is_candidate(c)]
    candidate_ids = [c.id for c in candidates]
    kept_ids = [c.id for c in children if not is_candidate(c)]

    if dry_run:
        return {
            "epic_id": epic_id,
            "epic_title": epic.title,
            "process_requirement_type": process["requirement_type"],
            "candidates_to_remove": candidate_ids,
            "children_kept_not_candidates": kept_ids,
            "historias_to_create": [
                {"titulo": h["titulo"], "story_points": h["story_points"], "fit_gap": h["fit_gap"],
                 "tags": build_tags(h)}
                for h in historias
            ],
        }

    removed = []
    for item in candidates:
        try:
            retire_candidate(client, item, process)
            removed.append(item.id)
        except AdoError as exc:
            print(f"  ⚠️  No se pudo retirar la candidata #{item.id}: {exc.message}", file=sys.stderr)

    created = []
    for h in historias:
        fields = {
            "Title": h["titulo"],
            "Description": build_story_description(h),
            process["effort_field"]: h["story_points"],
            "Tags": build_tags(h),
        }
        story = client.create_work_item(process["requirement_type"], fields)
        client.link_work_items(parent_id=epic_id, child_id=story.id)
        created.append({"id": story.id, "titulo": h["titulo"], "url": story.url})

    return {
        "epic_id": epic_id,
        "epic_title": epic.title,
        "candidates_removed": removed,
        "historias_created": created,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--organization", default=os.environ.get("ADO_ORG"))
    parser.add_argument("--project", default=os.environ.get("ADO_PROJECT"))
    parser.add_argument("--epic-id", required=True, type=int)
    parser.add_argument("--historias-json", required=True)
    parser.add_argument("--dry-run", action="store_true")
    add_process_argument(parser)
    args = parser.parse_args()

    if not args.process:
        print("ERROR: falta --process (agile | scrum | basic | cmmi) o ADO_PROCESS. Se ve en "
              "Azure DevOps → Project settings → Process. No se asume Agile.", file=sys.stderr)
        return 1
    process = get_process(args.process)

    if not args.organization or not args.project:
        print("ERROR: falta --organization/--project o ADO_ORG/ADO_PROJECT.", file=sys.stderr)
        return 1

    with open(args.historias_json, encoding="utf-8") as f:
        historias = json.load(f)

    errors = validate_historias(historias)
    if errors:
        print("ERROR: el input tiene problemas, no se escribe nada:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    pat = os.environ.get("ADO_PAT")
    if not pat and not args.dry_run:
        print("ERROR: falta ADO_PAT.", file=sys.stderr)
        return 1

    client = AdoClient(organization=args.organization, project=args.project, pat=pat or "dry-run")

    try:
        result = refine_epic(client, args.epic_id, historias, args.dry_run, process)
    except AdoError as exc:
        print(f"ERROR consultando/escribiendo en Azure DevOps: {exc.message}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
