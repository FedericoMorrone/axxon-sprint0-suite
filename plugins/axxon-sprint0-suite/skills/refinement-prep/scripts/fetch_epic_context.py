"""
fetch_epic_context.py — Trae el estado actual de una Épica y sus Stories hijas desde Azure
DevOps, para que refinement-prep arme el brief de la sesión sobre datos reales (no la tabla
estática del Kickoff Brief, que puede haber quedado desactualizada).

Solo lectura — nunca modifica nada en Azure DevOps.

Uso:
    python fetch_epic_context.py --organization axxon --project ClienteX --epic-id 1234
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from ado_client import AdoClient, AdoError
from process_map import read_effort

CHILD_LINK_TYPE = "System.LinkTypes.Hierarchy-Forward"


def extract_child_ids(epic_relations: list[dict]) -> list[int]:
    ids = []
    for rel in epic_relations:
        if rel.get("rel") == CHILD_LINK_TYPE:
            url = rel.get("url", "")
            # .../_apis/wit/workItems/1235
            tail = url.rstrip("/").rsplit("/", 1)[-1]
            if tail.isdigit():
                ids.append(int(tail))
    return ids


def fetch_epic_context(client: AdoClient, epic_id: int) -> dict:
    epic = client.get_work_item(epic_id, expand="relations")
    child_ids = extract_child_ids(epic.relations)
    children = client.get_work_items_batch(child_ids, expand="all") if child_ids else []

    return {
        "epic": {
            "id": epic.id,
            "title": epic.title,
            "state": epic.state,
            "description": epic.fields.get("System.Description", ""),
            "tags": epic.fields.get("System.Tags", ""),  # el Enfoque original vive acá
            "url": epic.url,
        },
        "stories": [
            {
                "id": s.id,
                "title": s.title,
                "state": s.state,
                "story_points": read_effort(s.fields),  # Story Points / Effort / Size según el proceso
                "description": s.fields.get("System.Description", ""),
                # Comentarios agregados manualmente desde que backlog-seeder las creó, si los hay:
                "comment_count": s.fields.get("System.CommentCount", 0),
                "url": s.url,
            }
            for s in children
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--organization", default=os.environ.get("ADO_ORG"))
    parser.add_argument("--project", default=os.environ.get("ADO_PROJECT"))
    parser.add_argument("--epic-id", required=True, type=int)
    args = parser.parse_args()

    if not args.organization or not args.project:
        print("ERROR: falta --organization/--project o las variables ADO_ORG/ADO_PROJECT.", file=sys.stderr)
        return 1

    pat = os.environ.get("ADO_PAT")
    if not pat:
        print("ERROR: falta la variable de entorno ADO_PAT.", file=sys.stderr)
        return 1

    client = AdoClient(organization=args.organization, project=args.project, pat=pat)

    try:
        context = fetch_epic_context(client, args.epic_id)
    except AdoError as exc:
        print(f"ERROR consultando Azure DevOps: {exc.message}", file=sys.stderr)
        return 1

    print(json.dumps(context, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
