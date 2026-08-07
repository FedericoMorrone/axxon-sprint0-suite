"""
build_recalibration.py — Compara el peso original de Fase 0 (guardado por backlog-seeder como
tag "fase0-peso-{n}" en cada Épica) contra la suma real de story points de Fase 1 (Historias
reales, escritas por backlog-refiner, identificables por su tag "fit-gap-*"). Reporta el
delta agregado de todo el proyecto, con un desglose por Épica como soporte.

Solo lectura — nunca modifica nada.

Uso:
    python build_recalibration.py --organization axxon --project ClienteX
"""

from __future__ import annotations

import argparse
import os
import re
import sys

from ado_client import AdoClient, AdoError

FASE0_PESO_RE = re.compile(r"fase0-peso-(\d+)")
PARENT_LINK_TYPE = "System.LinkTypes.Hierarchy-Reverse"


def extract_fase0_peso(tags: str) -> int | None:
    m = FASE0_PESO_RE.search(tags)
    return int(m.group(1)) if m else None


def fetch_epics_with_fase0_peso(client: AdoClient, project: str) -> dict[int, dict]:
    query = f"""
    SELECT [System.Id] FROM WorkItems
    WHERE [System.TeamProject] = '{project}' AND [System.WorkItemType] = 'Epic'
    """
    result = client.run_wiql(query)
    if not result.work_item_ids:
        return {}
    epics = client.get_work_items_batch(result.work_item_ids)
    out = {}
    for e in epics:
        peso = extract_fase0_peso(e.fields.get("System.Tags", ""))
        out[e.id] = {"title": e.title, "fase0_peso": peso, "fase1_total": 0, "story_count": 0}
    return out


def fetch_refined_stories(client: AdoClient, project: str) -> list:
    query = f"""
    SELECT [System.Id] FROM WorkItems
    WHERE [System.TeamProject] = '{project}'
      AND [System.WorkItemType] = 'User Story'
      AND [System.Tags] CONTAINS 'fit-gap-'
    """
    result = client.run_wiql(query)
    if not result.work_item_ids:
        return []
    return client.get_work_items_batch(result.work_item_ids, expand="relations")


def aggregate(epics: dict[int, dict], stories: list) -> dict[int, dict]:
    for s in stories:
        points = s.fields.get("Microsoft.VSTS.Scheduling.StoryPoints") or 0
        for rel in s.relations:
            if rel.get("rel") == PARENT_LINK_TYPE:
                parent_id = int(rel["url"].rstrip("/").rsplit("/", 1)[-1])
                if parent_id in epics:
                    epics[parent_id]["fase1_total"] += points
                    epics[parent_id]["story_count"] += 1
                break
    return epics


def build_markdown(epics: dict[int, dict], project: str) -> str:
    lines = [
        f"# Recalibración de Esfuerzo — {project}",
        "",
        "Compara el peso estimado en Fase 0 (Kickoff Brief, a nivel de proceso BPC macro)",
        "contra la suma real de story points de Fase 1 (Historias ya refinadas y",
        "confirmadas con el equipo). Es un agregado de **todo el proyecto**, corrido al",
        "cierre de Fase 1.",
        "",
        "| Épica | Peso Fase 0 | Total Fase 1 | Historias | Delta | Delta % |",
        "|---|---|---|---|---|---|",
    ]

    total_fase0 = 0
    total_fase1 = 0
    sin_baseline = []

    for epic_id, data in epics.items():
        fase0 = data["fase0_peso"]
        fase1 = data["fase1_total"]
        if fase0 is None:
            sin_baseline.append(data["title"])
            fase0_display = "sin dato"
            delta_display = "—"
            delta_pct_display = "—"
        else:
            total_fase0 += fase0
            delta = fase1 - fase0
            delta_pct = f"{(delta / fase0 * 100):+.0f}%" if fase0 else "—"
            fase0_display = str(fase0)
            delta_display = f"{delta:+d}"
            delta_pct_display = delta_pct
        if data["story_count"] > 0:
            total_fase1 += fase1
        lines.append(
            f"| {data['title']} | {fase0_display} | {fase1 or '—'} | "
            f"{data['story_count']} | {delta_display} | {delta_pct_display} |"
        )

    delta_total = total_fase1 - total_fase0
    delta_total_pct = f"{(delta_total / total_fase0 * 100):+.0f}%" if total_fase0 else "—"

    lines += [
        "",
        "## Totales del proyecto",
        "",
        f"- **Peso original Fase 0:** {total_fase0} puntos",
        f"- **Total real Fase 1:** {total_fase1} puntos",
        f"- **Delta:** {delta_total:+d} puntos ({delta_total_pct})",
        "",
    ]

    if sin_baseline:
        lines += [
            "## ⚠️ Épicas sin línea base de Fase 0",
            "",
            "Estas Épicas no tienen el tag `fase0-peso-*` — probablemente se crearon fuera",
            "del flujo de `backlog-seeder`, o son anteriores al fix que empezó a guardarlo.",
            "No entran en el total comparado arriba:",
            "",
        ]
        lines += [f"- {t}" for t in sin_baseline]
        lines.append("")

    lines += [
        "## Cómo leer el delta",
        "",
        "Un delta positivo grande en una Épica suele coincidir con Historias clasificadas",
        "`not-covered`/`partially-covered` en el rollup de `fit-gap-rollup` — cruzar ambos",
        "documentos antes de comunicar el número al cliente, no presentarlo aislado.",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--organization", default=os.environ.get("ADO_ORG"))
    parser.add_argument("--project", default=os.environ.get("ADO_PROJECT"))
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
        epics = fetch_epics_with_fase0_peso(client, args.project)
        stories = fetch_refined_stories(client, args.project)
        epics = aggregate(epics, stories)
    except AdoError as exc:
        print(f"ERROR consultando Azure DevOps: {exc.message}", file=sys.stderr)
        return 1

    print(build_markdown(epics, args.project))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
