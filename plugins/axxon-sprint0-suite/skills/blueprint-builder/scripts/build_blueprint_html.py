"""
build_blueprint_html.py — Genera el Solution Blueprint (cierre de Fase 1) como HTML con la
marca Axxon 2025, estructurado según las 10 áreas oficiales del Solution Blueprint Review de
Microsoft Success by Design (learn.microsoft.com/dynamics365/guidance/fasttrack/solution-workshops):

  1. Program strategy              6. Business process strategy
  2. Application strategy          7. Security strategy
  3. Data strategy                 8. Application lifecycle management strategy
  4. Integration strategy          9. Environment and capacity strategy
  5. Test strategy                10. Intelligence strategy

Enfoque MIXTO: 2 áreas (Business process strategy, Environment & capacity strategy) se
auto-completan leyendo Azure DevOps y `.d365-project.md` — son datos ya estructurados y
consultables. Las otras 8 las arma Claude sintetizando lo que haya disponible (Kickoff Brief,
FDDs ya generados, notas, transcripciones) ANTES de llamar a este script — este módulo solo
renderiza, no decide contenido salvo en las 2 áreas automáticas.

Ninguna área queda nunca en blanco sin decirlo: si no hay fuente, el status es
"requiere-intervencion-humana" — eso NO es lo mismo que "pendiente, se define después" (como
en el FDD) — es una señal de que hay que preguntarle algo al usuario antes de dar el
documento por terminado. Ver SKILL.md para el protocolo exacto.
"""

from __future__ import annotations

import base64
import html as html_lib
import re
from pathlib import Path

from ado_client import AdoClient, AdoError

ASSETS_DIR = Path(__file__).parent.parent / "assets"
FASE0_PESO_RE = re.compile(r"fase0-peso-(\d+)")
FIT_GAP_TAGS = ["fit-gap-fully-covered", "fit-gap-partially-covered", "fit-gap-not-covered"]
PARENT_LINK_TYPE = "System.LinkTypes.Hierarchy-Reverse"

SBD_AREAS = [
    ("program", "1. Program Strategy"),
    ("application", "2. Application Strategy"),
    ("data", "3. Data Strategy"),
    ("integration", "4. Integration Strategy"),
    ("test", "5. Test Strategy"),
    ("business_process", "6. Business Process Strategy"),
    ("security", "7. Security Strategy"),
    ("alm", "8. Application Lifecycle Management Strategy"),
    ("environment", "9. Environment & Capacity Strategy"),
    ("intelligence", "10. Intelligence Strategy"),
]

STATUS_LABELS = {
    "completo": ("Completo", "status-ok"),
    "parcial": ("Parcial", "status-partial"),
    "requiere-intervencion-humana": ("Requiere intervención humana", "status-blocked"),
}


def _esc(value) -> str:
    return html_lib.escape(str(value)) if value is not None else ""


def _logo_b64(filename: str) -> str:
    return base64.b64encode((ASSETS_DIR / filename).read_bytes()).decode()


# ---------------------------------------------------------------------------
# Auto-completado — Business Process Strategy (desde Azure DevOps)
# ---------------------------------------------------------------------------

def extract_classification(tags: str) -> str | None:
    for tag in FIT_GAP_TAGS:
        if tag in tags:
            return tag.replace("fit-gap-", "")
    return None


def fetch_business_process_strategy(client: AdoClient, project: str) -> dict:
    """Reusa el mismo patrón de consulta que effort-recalibration/fit-gap-rollup — procesos
    BPC (Épicas) + su cobertura fit/gap real, ya en Azure DevOps."""
    query = f"""
    SELECT [System.Id] FROM WorkItems
    WHERE [System.TeamProject] = '{project}' AND [System.WorkItemType] = 'Epic'
    """
    result = client.run_wiql(query)
    if not result.work_item_ids:
        return {"status": "requiere-intervencion-humana", "epics": [], "source": "Azure DevOps (sin Épicas encontradas)"}

    epics = client.get_work_items_batch(result.work_item_ids)
    story_query = f"""
    SELECT [System.Id] FROM WorkItems
    WHERE [System.TeamProject] = '{project}'
      AND [System.WorkItemType] = 'User Story'
      AND [System.Tags] CONTAINS 'fit-gap-'
    """
    story_result = client.run_wiql(story_query)
    stories = client.get_work_items_batch(story_result.work_item_ids, expand="relations") if story_result.work_item_ids else []

    coverage_by_epic: dict[int, dict[str, int]] = {e.id: {"fully-covered": 0, "partially-covered": 0, "not-covered": 0} for e in epics}
    for s in stories:
        classification = extract_classification(s.fields.get("System.Tags", ""))
        if not classification:
            continue
        for rel in s.relations:
            if rel.get("rel") == PARENT_LINK_TYPE:
                parent_id = int(rel["url"].rstrip("/").rsplit("/", 1)[-1])
                if parent_id in coverage_by_epic:
                    coverage_by_epic[parent_id][classification] += 1
                break

    epic_rows = [
        {"title": e.title, "coverage": coverage_by_epic.get(e.id, {})}
        for e in epics
    ]
    status = "completo" if stories else "parcial"
    return {"status": status, "epics": epic_rows, "source": f"Azure DevOps — Project {project}"}


# ---------------------------------------------------------------------------
# Auto-completado — Environment & Capacity Strategy (desde .d365-project.md)
# ---------------------------------------------------------------------------

def fetch_environment_capacity_strategy(project_context_path: str) -> dict:
    path = Path(project_context_path)
    if not path.exists():
        return {"status": "requiere-intervencion-humana", "dataverse": {}, "ado": {}, "source": ".d365-project.md no existe"}

    text = path.read_text(encoding="utf-8")
    dataverse = {}
    dv_section = re.search(r"## Dataverse\n(.*?)(?=\n## |\Z)", text, re.DOTALL)
    if dv_section:
        for env in ("DEV", "TEST", "PROD"):
            m = re.search(rf"-\s*{env}:\s*(\S+)", dv_section.group(1))
            dataverse[env] = m.group(1) if m else None

    ado = {}
    ado_section = re.search(r"## Azure DevOps.*?\n(.*?)(?=\n## |\Z)", text, re.DOTALL)
    if ado_section:
        for field, label in [("organizacion", "Organización"), ("project", "Project"), ("repo", "Repo")]:
            m = re.search(rf"-\s*{label}:\s*(.+)", ado_section.group(1))
            ado[field] = m.group(1).strip() if m else None

    subs = []
    sub_section = re.search(r"## Azure — suscripciones\n(.*?)(?=\n## |\Z)", text, re.DOTALL)
    if sub_section:
        subs = [line.strip("- ").strip() for line in sub_section.group(1).splitlines() if line.strip().startswith("-")]

    complete = all(dataverse.values()) and all(ado.values()) and subs
    status = "completo" if complete else "parcial"
    return {"status": status, "dataverse": dataverse, "ado": ado, "subscriptions": subs, "source": ".d365-project.md"}


# ---------------------------------------------------------------------------
# HTML — marca Axxon 2025 (mismo patrón que fdd-builder / effort-recalibration)
# ---------------------------------------------------------------------------

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&display=swap');

:root {
  --axx-blue: #000FC4; --axx-navy: #002060; --axx-bg: #FFFFFF; --axx-text: #0C0C0C;
  --axx-muted: #6B6B6B; --axx-border: #E0E0E0; --axx-green: #177E44; --axx-orange: #F06D26;
  --axx-red: #E30082;
}
* { box-sizing: border-box; }
body { font-family: 'Segoe UI', sans-serif; color: var(--axx-text); background: var(--axx-bg); margin: 0; line-height: 1.6; }
.doc { max-width: 960px; margin: 0 auto; padding: 0 32px 64px; }

.doc-header { display: flex; justify-content: space-between; align-items: flex-start; padding: 48px 0 8px; }
.doc-logo { height: 30px; }
.doc-title-block h1 {
  font-family: 'Bebas Neue', sans-serif; font-weight: 400; letter-spacing: 0.5px;
  color: var(--axx-blue); text-transform: uppercase; font-size: 40px; margin: 0 0 4px;
}
.doc-title-block p { color: var(--axx-muted); margin: 0; font-size: 14px; }

.toc { background: #F7F8FC; border-radius: 8px; padding: 20px 24px; margin: 32px 0; }
.toc h2 { font-size: 14px; text-transform: uppercase; color: var(--axx-muted); margin: 0 0 12px; }
.toc ul { columns: 2; margin: 0; padding-left: 20px; font-size: 14px; }
.toc a { color: var(--axx-text); text-decoration: none; }
.toc a:hover { color: var(--axx-blue); }

.area-section { margin: 40px 0; page-break-inside: avoid; }
.area-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 3px solid var(--axx-blue); padding-bottom: 8px; margin-bottom: 12px; }
.area-header h2 {
  font-family: 'Bebas Neue', sans-serif; font-weight: 400; letter-spacing: 0.5px;
  color: var(--axx-navy); text-transform: uppercase; font-size: 24px; margin: 0;
}
.status-badge { padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; white-space: nowrap; }
.status-ok { background: #E3F3E9; color: var(--axx-green); }
.status-partial { background: #FDEEE3; color: var(--axx-orange); }
.status-blocked { background: #FBE3EC; color: var(--axx-red); }
.area-source { color: var(--axx-muted); font-size: 12px; margin: 0 0 12px; }
.area-content { font-size: 14px; }
.area-content p { margin: 8px 0; }
.area-content ul { margin: 8px 0; padding-left: 22px; }

.axx-table { width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 14px; }
.axx-table th { background: var(--axx-navy); color: white; text-align: left; padding: 8px 12px; font-weight: 600; }
.axx-table td { padding: 8px 12px; border-bottom: 1px solid var(--axx-border); }
.axx-table tr:nth-child(even) td { background: #F7F8FC; }
.axx-table td.num { text-align: right; }

.blocked-box {
  background: #FBE3EC; border-left: 4px solid var(--axx-red); padding: 14px 18px;
  font-size: 14px; border-radius: 4px;
}
.blocked-box strong { color: var(--axx-red); }

.doc-footer { display: flex; justify-content: space-between; align-items: center; margin-top: 64px; padding-top: 24px; border-top: 1px solid var(--axx-border); }
.doc-footer img { height: 20px; }
.doc-footer .url { color: var(--axx-muted); font-size: 12px; }
"""


def _business_process_html(area: dict) -> str:
    if not area.get("epics"):
        return '<div class="blocked-box"><strong>Sin datos</strong> — no se encontraron Épicas en Azure DevOps.</div>'
    rows = ""
    for e in area["epics"]:
        cov = e["coverage"]
        total = sum(cov.values()) or 1
        rows += (f"<tr><td>{_esc(e['title'])}</td>"
                 f"<td class='num'>{cov.get('fully-covered', 0)} ({cov.get('fully-covered',0)/total*100:.0f}%)</td>"
                 f"<td class='num'>{cov.get('partially-covered', 0)} ({cov.get('partially-covered',0)/total*100:.0f}%)</td>"
                 f"<td class='num'>{cov.get('not-covered', 0)} ({cov.get('not-covered',0)/total*100:.0f}%)</td></tr>")
    return (f'<table class="axx-table"><thead><tr><th>Proceso BPC (Épica)</th>'
            f'<th>Fully-covered</th><th>Partially-covered</th><th>Not-covered</th></tr></thead>'
            f'<tbody>{rows}</tbody></table>')


def _environment_html(area: dict) -> str:
    dv = area.get("dataverse", {})
    ado = area.get("ado", {})
    subs = area.get("subscriptions", [])
    rows = "".join(f"<tr><td>Dataverse {env}</td><td>{_esc(url) if url else '<em>falta</em>'}</td></tr>" for env, url in dv.items())
    rows += f"<tr><td>Azure DevOps</td><td>{_esc(ado.get('organizacion'))} / {_esc(ado.get('project'))} / {_esc(ado.get('repo'))}</td></tr>"
    for i, s in enumerate(subs, 1):
        rows += f"<tr><td>Suscripción Azure #{i}</td><td>{_esc(s)}</td></tr>"
    return f'<table class="axx-table"><tbody>{rows}</tbody></table>'


def render_html(data: dict, project_name: str) -> str:
    """`data` es un dict con una entrada por área SBD (ver SBD_AREAS). Cada entrada:
    {"status": "completo"|"parcial"|"requiere-intervencion-humana",
     "content_html": "<p>...</p>" (HTML ya armado por Claude o por las funciones fetch_*),
     "source": "de dónde salió este contenido"}
    """
    toc_items = "".join(f'<li><a href="#{key}">{label}</a></li>' for key, label in SBD_AREAS)

    sections = ""
    blocked_count = 0
    for key, label in SBD_AREAS:
        area = data.get(key, {"status": "requiere-intervencion-humana", "content_html": "", "source": "No provisto"})
        status_label, status_class = STATUS_LABELS.get(area["status"], STATUS_LABELS["requiere-intervencion-humana"])
        if area["status"] == "requiere-intervencion-humana":
            blocked_count += 1
            content = (f'<div class="blocked-box"><strong>Requiere intervención humana.</strong> '
                       f'No hay información suficiente en las fuentes disponibles para completar esta '
                       f'área — hace falta que alguien del equipo la complete antes del cierre formal '
                       f'de Fase 1.</div>')
        else:
            content = area.get("content_html", "")
        sections += (f'<section class="area-section" id="{key}">'
                     f'<div class="area-header"><h2>{_esc(label)}</h2>'
                     f'<span class="status-badge {status_class}">{status_label}</span></div>'
                     f'<p class="area-source">Fuente: {_esc(area.get("source", "—"))}</p>'
                     f'<div class="area-content">{content}</div></section>')

    logo_axxon = _logo_b64("logo-axxon.png")
    logo_ed = _logo_b64("logo-evolucion-digital.png")

    summary_note = ""
    if blocked_count:
        summary_note = (f'<div class="blocked-box" style="margin: 24px 0;">'
                        f'<strong>{blocked_count} de 10 áreas requieren intervención humana</strong> '
                        f'antes de que este Blueprint pueda considerarse cerrado — no es un documento '
                        f'final todavía, es un borrador de trabajo.</div>')

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8" />
<title>Solution Blueprint — {_esc(project_name)}</title>
<style>{CSS}</style>
</head>
<body>
<div class="doc">
  <header class="doc-header">
    <div class="doc-title-block">
      <h1>Solution Blueprint</h1>
      <p>Cierre de Fase 1 · Plan — Proyecto {_esc(project_name)} · Según Success by Design (Microsoft)</p>
    </div>
    <img class="doc-logo" src="data:image/png;base64,{logo_axxon}" alt="Axxon" />
  </header>

  {summary_note}

  <nav class="toc">
    <h2>Índice — 10 áreas del Solution Blueprint Review</h2>
    <ul>{toc_items}</ul>
  </nav>

  {sections}

  <footer class="doc-footer">
    <img src="data:image/png;base64,{logo_ed}" alt="Evolución Digital" />
    <span class="url">www.axxonconsulting.com</span>
  </footer>
</div>
</body>
</html>"""


def save(html_content: str, path: str) -> None:
    Path(path).write_text(html_content, encoding="utf-8")
