"""
build_fitgap_rollup.py — Agrega la clasificación fit/gap (fully-covered / partially-covered /
not-covered) de todas las Historias reales de una Épica (o de todo el proyecto) en un solo
reporte. Lee exclusivamente el tag "fit-gap-{clasificación}" que `backlog-refiner` escribe en
cada Historia real — no clasifica nada por su cuenta, solo agrega lo que ya está en ADO.

Solo lectura — nunca modifica nada.

Uso:
    python build_fitgap_rollup.py --organization axxon --project ClienteX
    python build_fitgap_rollup.py --organization axxon --project ClienteX --epic-id 1234
"""

from __future__ import annotations

import argparse
import os
import sys

from ado_client import AdoClient, AdoError

FIT_GAP_TAGS = ["fit-gap-fully-covered", "fit-gap-partially-covered", "fit-gap-not-covered"]
CHILD_LINK_TYPE = "System.LinkTypes.Hierarchy-Forward"
PARENT_LINK_TYPE = "System.LinkTypes.Hierarchy-Reverse"


def extract_classification(tags: str) -> str | None:
    for tag in FIT_GAP_TAGS:
        if tag in tags:
            return tag.replace("fit-gap-", "")
    return None


def fetch_stories_for_epic(client: AdoClient, epic_id: int) -> list:
    epic = client.get_work_item(epic_id, expand="relations")
    child_ids = [
        int(rel["url"].rstrip("/").rsplit("/", 1)[-1])
        for rel in epic.relations
        if rel.get("rel") == CHILD_LINK_TYPE
    ]
    stories = client.get_work_items_batch(child_ids, expand="all") if child_ids else []
    return [(epic.title, s) for s in stories]


def fetch_all_stories_with_fitgap(client: AdoClient, project: str) -> list:
    """Trae todas las User Stories del proyecto que tengan un tag fit-gap-* — vía WIQL, sin
    necesitar el ID de cada Épica de antemano."""
    query = f"""
    SELECT [System.Id] FROM WorkItems
    WHERE [System.TeamProject] = '{project}'
      AND [System.WorkItemType] = 'User Story'
      AND [System.Tags] CONTAINS 'fit-gap-'
    """
    result = client.run_wiql(query)
    if not result.work_item_ids:
        return []
    stories = client.get_work_items_batch(result.work_item_ids, expand="relations")

    rows = []
    for s in stories:
        epic_title = "(Épica no encontrada)"
        for rel in s.relations:
            if rel.get("rel") == PARENT_LINK_TYPE:
                parent_id = int(rel["url"].rstrip("/").rsplit("/", 1)[-1])
                try:
                    parent = client.get_work_item(parent_id)
                    epic_title = parent.title
                except AdoError:
                    pass
                break
        rows.append((epic_title, s))
    return rows


def build_markdown(rows: list, scope_label: str) -> str:
    counts = {"fully-covered": 0, "partially-covered": 0, "not-covered": 0, "sin clasificar": 0}
    lines = [
        f"# FIT/GAP Rollup — {scope_label}",
        "",
        "Agregado de las clasificaciones fit/gap ya registradas en Azure DevOps por",
        "`backlog-refiner` — este reporte no clasifica nada, solo junta lo existente.",
        "",
        "| Épica | Historia | Clasificación | Story Points |",
        "|---|---|---|---|",
    ]
    for epic_title, story in rows:
        classification = extract_classification(story.fields.get("System.Tags", "")) or "sin clasificar"
        counts[classification] = counts.get(classification, 0) + 1
        points = story.fields.get("Microsoft.VSTS.Scheduling.StoryPoints", "—")
        lines.append(f"| {epic_title} | {story.title} | {classification} | {points} |")

    total = sum(counts.values())
    lines += [
        "",
        "## Resumen",
        "",
        f"Total de Historias clasificadas: {total}",
        "",
        "| Clasificación | Cantidad | % |",
        "|---|---|---|",
    ]
    for label, n in counts.items():
        pct = f"{(n / total * 100):.0f}%" if total else "—"
        lines.append(f"| {label} | {n} | {pct} |")

    lines += [
        "",
        "> Nota: este documento es de trabajo (Markdown). Si hace falta una versión formal",
        "> para el cliente, se puede transformar a Word/PowerPoint con el template de marca",
        "> Axxon como paso posterior — no lo hace esta skill.",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--organization", default=os.environ.get("ADO_ORG"))
    parser.add_argument("--project", default=os.environ.get("ADO_PROJECT"))
    parser.add_argument("--epic-id", type=int, default=None,
                         help="Si se omite, agrega TODO el proyecto")
    args = parser.parse_args()

    if not args.organization or not args.project:
        print("ERROR: falta --organization/--project o ADO_ORG/ADO_PROJECT.", file=sys.stderr)
        return 1

    pat = os.environ.get("ADO_PAT")
    if not pat:
        print("ERROR: falta ADO_PAT.", file=sys.stderr)
        return 1

    client = AdoClient(organization=args.organization, project=args.project, pat=pat)

    try:
        if args.epic_id:
            rows = fetch_stories_for_epic(client, args.epic_id)
            scope_label = f"Épica #{args.epic_id}"
        else:
            rows = fetch_all_stories_with_fitgap(client, args.project)
            scope_label = f"Proyecto {args.project} (completo)"
    except AdoError as exc:
        print(f"ERROR consultando Azure DevOps: {exc.message}", file=sys.stderr)
        return 1

    print(build_markdown(rows, scope_label))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
