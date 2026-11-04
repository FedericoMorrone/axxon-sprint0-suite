"""
build_recalibration.py — Cierre de Fase 1: compara el peso original de Fase 0 (tag
"fase0-peso-{n}" en cada Épica) contra la suma real de story points de Fase 1, y agrega la
clasificación fit/gap final de todas las Historias reales — todo en un solo reporte HTML con
la marca Axxon 2025 (misma paleta/tipografía que el template PPTX de kickoff-brief y el FDD).

Agregado de todo el proyecto, corrido una vez al cierre de Fase 1. Solo lectura — nunca
modifica nada en Azure DevOps.

Uso:
    python build_recalibration.py --organization axxon --project ClienteX
"""

from __future__ import annotations

import argparse
import base64
import html as html_lib
import os
import re
import sys
from pathlib import Path

from ado_client import AdoClient, AdoError
from process_map import REQUIREMENT_CATEGORY_WIQL, read_effort

FASE0_PESO_RE = re.compile(r"fase0-peso-(\d+)")
PARENT_LINK_TYPE = "System.LinkTypes.Hierarchy-Reverse"
FIT_GAP_TAGS = ["fit-gap-fully-covered", "fit-gap-partially-covered", "fit-gap-not-covered"]
ASSETS_DIR = Path(__file__).parent.parent / "assets"


def _esc(value) -> str:
    return html_lib.escape(str(value)) if value is not None else "—"


def _logo_b64(filename: str) -> str:
    return base64.b64encode((ASSETS_DIR / filename).read_bytes()).decode()


# ---------------------------------------------------------------------------
# Data fetching (solo lectura)
# ---------------------------------------------------------------------------

def extract_fase0_peso(tags: str) -> int | None:
    m = FASE0_PESO_RE.search(tags)
    return int(m.group(1)) if m else None


def extract_classification(tags: str) -> str | None:
    for tag in FIT_GAP_TAGS:
        if tag in tags:
            return tag.replace("fit-gap-", "")
    return None


def fetch_epics_with_fase0_peso(client: AdoClient, project: str) -> dict[int, dict]:
    query = f"""
    SELECT [System.Id] FROM WorkItems
    WHERE [System.TeamProject] = '{project}' AND [System.WorkItemType] = 'Epic'
    """
    result = client.run_wiql(query)
    if not result.work_item_ids:
        return {}
    epics = client.get_work_items_batch(result.work_item_ids)
    return {
        e.id: {"title": e.title, "fase0_peso": extract_fase0_peso(e.fields.get("System.Tags", "")),
               "fase1_total": 0, "story_count": 0}
        for e in epics
    }


def fetch_refined_stories(client: AdoClient, project: str) -> list:
    """Historias reales (con tag fit-gap-*, escritas por backlog-refiner). expand='relations'
    trae también los fields normales (Title, Tags, StoryPoints) — no hace falta una query aparte
    para el rollup de fit/gap, se lee de la misma lista."""
    query = f"""
    SELECT [System.Id] FROM WorkItems
    WHERE [System.TeamProject] = '{project}'
      AND {REQUIREMENT_CATEGORY_WIQL}
      AND [System.Tags] CONTAINS 'fit-gap-'
    """
    result = client.run_wiql(query)
    if not result.work_item_ids:
        return []
    return client.get_work_items_batch(result.work_item_ids, expand="relations")


def aggregate(epics: dict[int, dict], stories: list) -> tuple[dict[int, dict], list[dict]]:
    """Devuelve (epics actualizado con totales de Fase 1, filas de fit/gap por Historia)."""
    fitgap_rows = []
    for s in stories:
        points = read_effort(s.fields) or 0
        classification = extract_classification(s.fields.get("System.Tags", "")) or "sin clasificar"
        epic_title = "(Épica no encontrada)"
        for rel in s.relations:
            if rel.get("rel") == PARENT_LINK_TYPE:
                parent_id = int(rel["url"].rstrip("/").rsplit("/", 1)[-1])
                if parent_id in epics:
                    epics[parent_id]["fase1_total"] += points
                    epics[parent_id]["story_count"] += 1
                    epic_title = epics[parent_id]["title"]
                break
        fitgap_rows.append({
            "id": s.id, "epic": epic_title, "story": s.title,
            "classification": classification, "points": points,
        })
    return epics, fitgap_rows


# ---------------------------------------------------------------------------
# HTML — misma marca Axxon 2025 que fdd-builder
# ---------------------------------------------------------------------------

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&display=swap');

:root {
  --axx-blue: #000FC4;
  --axx-navy: #002060;
  --axx-bg: #FFFFFF;
  --axx-text: #0C0C0C;
  --axx-muted: #6B6B6B;
  --axx-border: #E0E0E0;
  --axx-green: #177E44;
  --axx-orange: #F06D26;
}
* { box-sizing: border-box; }
body {
  font-family: 'Segoe UI', sans-serif; color: var(--axx-text); background: var(--axx-bg);
  margin: 0; line-height: 1.6;
}
.doc { max-width: 960px; margin: 0 auto; padding: 0 32px 64px; }

.doc-header { display: flex; justify-content: space-between; align-items: flex-start; padding: 48px 0 32px; }
.doc-logo { height: 30px; }
.doc-title-block h1 {
  font-family: 'Bebas Neue', sans-serif; font-weight: 400; letter-spacing: 0.5px;
  color: var(--axx-blue); text-transform: uppercase; font-size: 40px; margin: 0 0 4px;
}
.doc-title-block p { color: var(--axx-muted); margin: 0; font-size: 14px; }

.summary-cards { display: table; width: 100%; margin: 24px 0 40px; border-spacing: 16px 0; }
.summary-card {
  display: table-cell; background: #F7F8FC; border-radius: 8px; padding: 20px;
  text-align: center; border-top: 4px solid var(--axx-blue);
}
.summary-card .value {
  font-family: 'Bebas Neue', sans-serif; font-size: 32px; color: var(--axx-navy); display: block;
}
.summary-card .label { color: var(--axx-muted); font-size: 12px; text-transform: uppercase; }
.summary-card.positive { border-top-color: var(--axx-orange); }
.summary-card.negative { border-top-color: var(--axx-green); }

.doc-section { margin: 48px 0; page-break-inside: avoid; }
.doc-section h2 {
  font-family: 'Bebas Neue', sans-serif; font-weight: 400; letter-spacing: 0.5px;
  color: var(--axx-navy); text-transform: uppercase; font-size: 26px;
  border-bottom: 3px solid var(--axx-blue); padding-bottom: 8px; margin-bottom: 8px;
}
.doc-section .section-intro { color: var(--axx-muted); font-size: 14px; margin-bottom: 16px; }

.axx-table { width: 100%; border-collapse: collapse; margin: 12px 0 24px; font-size: 14px; }
.axx-table th {
  background: var(--axx-navy); color: white; text-align: left; padding: 8px 12px; font-weight: 600;
}
.axx-table td { padding: 8px 12px; border-bottom: 1px solid var(--axx-border); }
.axx-table tr:nth-child(even) td { background: #F7F8FC; }
.axx-table td.num { text-align: right; font-variant-numeric: tabular-nums; }
.axx-table a { color: var(--axx-blue); text-decoration: none; font-weight: 600; }
.axx-table a:hover { text-decoration: underline; }
.delta-pos { color: var(--axx-orange); font-weight: 600; }
.delta-neg { color: var(--axx-green); font-weight: 600; }

.tag {
  display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: 600;
}
.tag.fully-covered { background: #E3F3E9; color: var(--axx-green); }
.tag.partially-covered { background: #FDEEE3; color: var(--axx-orange); }
.tag.not-covered { background: #FBE3EC; color: #E30082; }
.tag.sin-clasificar { background: #EEE; color: var(--axx-muted); }

.warning-box {
  background: #FFF8E1; border-left: 4px solid #F06D26; padding: 12px 16px; margin: 16px 0; font-size: 14px;
}
.read-note { color: var(--axx-muted); font-size: 13px; margin-top: 8px; }

.doc-footer {
  display: flex; justify-content: space-between; align-items: center;
  margin-top: 64px; padding-top: 24px; border-top: 1px solid var(--axx-border);
}
.doc-footer img { height: 20px; }
.doc-footer .url { color: var(--axx-muted); font-size: 12px; }
"""


def _epic_rows_html(epics: dict[int, dict]) -> tuple[str, int, int, list[str]]:
    rows, total_fase0, total_fase1, sin_baseline = "", 0, 0, []
    for data in epics.values():
        fase0, fase1 = data["fase0_peso"], data["fase1_total"]
        if fase0 is None:
            sin_baseline.append(data["title"])
            fase0_d, delta_d, pct_d = "sin dato", "—", "—"
        else:
            total_fase0 += fase0
            delta = fase1 - fase0
            pct = f"{(delta / fase0 * 100):+.0f}%" if fase0 else "—"
            cls = "delta-pos" if delta > 0 else ("delta-neg" if delta < 0 else "")
            fase0_d, delta_d, pct_d = str(fase0), f'<span class="{cls}">{delta:+d}</span>', f'<span class="{cls}">{pct}</span>'
        if data["story_count"] > 0:
            total_fase1 += fase1
        rows += (f"<tr><td>{_esc(data['title'])}</td><td class='num'>{fase0_d}</td>"
                 f"<td class='num'>{fase1 or '—'}</td><td class='num'>{data['story_count']}</td>"
                 f"<td class='num'>{delta_d}</td><td class='num'>{pct_d}</td></tr>")
    return rows, total_fase0, total_fase1, sin_baseline


def _ado_work_item_url(organization: str, project: str, work_item_id: int) -> str:
    """URL navegable en el browser — distinta a `WorkItem.url` (esa es el self-link de la
    REST API, no abre en Azure DevOps directamente)."""
    return f"https://dev.azure.com/{organization}/{project}/_workitems/edit/{work_item_id}"


def _fitgap_rows_html(fitgap_rows: list[dict], organization: str, project: str) -> tuple[str, dict]:
    rows = ""
    counts = {"fully-covered": 0, "partially-covered": 0, "not-covered": 0, "sin clasificar": 0}
    for r in fitgap_rows:
        counts[r["classification"]] = counts.get(r["classification"], 0) + 1
        tag_class = r["classification"].replace(" ", "-").replace("sin-clasificar", "sin-clasificar")
        story_url = _ado_work_item_url(organization, project, r["id"])
        story_link = f'<a href="{story_url}" target="_blank" rel="noopener">{_esc(r["story"])}</a>'
        rows += (f"<tr><td>{_esc(r['epic'])}</td><td>{story_link}</td>"
                 f"<td><span class='tag {tag_class}'>{_esc(r['classification'])}</span></td>"
                 f"<td class='num'>{r['points']}</td></tr>")
    return rows, counts


def render_html(epics: dict[int, dict], fitgap_rows: list[dict], project: str, organization: str) -> str:
    epic_rows, total_fase0, total_fase1, sin_baseline = _epic_rows_html(epics)
    fitgap_rows_html, counts = _fitgap_rows_html(fitgap_rows, organization, project)
    delta_total = total_fase1 - total_fase0
    delta_total_pct = f"{(delta_total / total_fase0 * 100):+.0f}%" if total_fase0 else "—"
    delta_card_class = "positive" if delta_total > 0 else ("negative" if delta_total < 0 else "")
    total_historias = sum(counts.values())

    warning = ""
    if sin_baseline:
        items = "".join(f"<li>{_esc(t)}</li>" for t in sin_baseline)
        warning = (f'<div class="warning-box"><strong>⚠️ Épicas sin línea base de Fase 0</strong> — '
                   f'no tienen el tag <code>fase0-peso-*</code>, no entran en el total comparado:'
                   f'<ul>{items}</ul></div>')

    fitgap_summary_rows = "".join(
        f"<tr><td>{label}</td><td class='num'>{n}</td>"
        f"<td class='num'>{(n/total_historias*100):.0f}%</td></tr>" if total_historias else ""
        for label, n in counts.items()
    )

    logo_axxon = _logo_b64("logo-axxon.png")
    logo_ed = _logo_b64("logo-evolucion-digital.png")

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8" />
<title>Recalibración de Esfuerzo — {_esc(project)}</title>
<style>{CSS}</style>
</head>
<body>
<div class="doc">
  <header class="doc-header">
    <div class="doc-title-block">
      <h1>Recalibración de Esfuerzo</h1>
      <p>Cierre de Fase 1 · Plan — Proyecto {_esc(project)}</p>
    </div>
    <img class="doc-logo" src="data:image/png;base64,{logo_axxon}" alt="Axxon" />
  </header>

  <div class="summary-cards">
    <div class="summary-card"><span class="value">{total_fase0}</span><span class="label">Peso Fase 0</span></div>
    <div class="summary-card"><span class="value">{total_fase1}</span><span class="label">Total Fase 1</span></div>
    <div class="summary-card {delta_card_class}"><span class="value">{delta_total:+d}</span><span class="label">Delta ({delta_total_pct})</span></div>
    <div class="summary-card"><span class="value">{total_historias}</span><span class="label">Historias refinadas</span></div>
  </div>

  <section class="doc-section">
    <h2>Recalibración por Épica</h2>
    <p class="section-intro">Peso estimado en Fase 0 (Kickoff Brief, proceso BPC macro) contra la suma real de story points de Fase 1, confirmados con el equipo.</p>
    <table class="axx-table">
      <thead><tr><th>Épica</th><th>Peso Fase 0</th><th>Total Fase 1</th><th>Historias</th><th>Delta</th><th>Delta %</th></tr></thead>
      <tbody>{epic_rows}</tbody>
    </table>
    {warning}
  </section>

  <section class="doc-section">
    <h2>Fit &amp; Gap Final</h2>
    <p class="section-intro">Clasificación de cobertura de todas las Historias reales del proyecto, ya registrada en Azure DevOps por backlog-refiner.</p>
    <table class="axx-table">
      <thead><tr><th>Épica</th><th>Historia</th><th>Clasificación</th><th>Puntos</th></tr></thead>
      <tbody>{fitgap_rows_html}</tbody>
    </table>
    <table class="axx-table" style="max-width: 420px;">
      <thead><tr><th>Clasificación</th><th>Cantidad</th><th>%</th></tr></thead>
      <tbody>{fitgap_summary_rows}</tbody>
    </table>
    <p class="read-note">Un delta positivo grande en una Épica suele coincidir con Historias
      clasificadas partially/not-covered arriba — leer ambas tablas juntas antes de comunicar
      el número al cliente, no presentar el delta aislado.</p>
  </section>

  <footer class="doc-footer">
    <img src="data:image/png;base64,{logo_ed}" alt="Evolución Digital" />
    <span class="url">www.axxonconsulting.com</span>
  </footer>
</div>
</body>
</html>"""


def save(html_content: str, path: str) -> None:
    Path(path).write_text(html_content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--organization", default=os.environ.get("ADO_ORG"))
    parser.add_argument("--project", default=os.environ.get("ADO_PROJECT"))
    parser.add_argument("--output", default=None, help="Path de salida .html (default: stdout del path generado en /tmp)")
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
        epics, fitgap_rows = aggregate(epics, stories)
    except AdoError as exc:
        print(f"ERROR consultando Azure DevOps: {exc.message}", file=sys.stderr)
        return 1

    html_out = render_html(epics, fitgap_rows, args.project, args.organization)
    output_path = args.output or f"Recalibracion-{args.project}.html"
    save(html_out, output_path)
    print(f"Generado: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
