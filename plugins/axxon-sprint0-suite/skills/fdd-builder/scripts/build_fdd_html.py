"""
build_fdd_html.py — Genera el Documento de Diseño Funcional (FDD) como HTML autocontenido,
con la marca real de Axxon (tipografía Poppins, azul #1E4BF0, navy #1F3864 — extraídos del
template Word original, ver assets/Plantilla_FDD_legacy_reference.docx). Reemplaza la
generación en Word de la versión anterior de esta skill.

El HTML resultante es un solo archivo (CSS embebido, logos embebidos en base64) — se abre en
cualquier navegador sin dependencias, y se puede imprimir a PDF desde ahí si hace falta.

Uso:
    from build_fdd_html import render_fdd, save
    html = render_fdd(data)  # data: ver estructura abajo
    save(html, "outputs/FDD-GAP-200-IntegracionSAP.html")

Estructura de `data` (dict) — todos los campos son opcionales salvo los marcados *obligatorio*;
lo que falte se muestra explícitamente como pendiente, nunca se inventa:

{
  "gap_id": "200",                      # *obligatorio*
  "gap_nombre": "Integración SAP",      # *obligatorio*
  "cliente": "Cliente X",               # *obligatorio*
  "proyecto_id": "PRU00000999",
  "autor": "Nombre del consultor",
  "fecha": "2026-08-07",
  "revisiones": [{"fecha": "...", "autor": "...", "detalle": "..."}],
  "introduccion": "texto libre",
  "alcance": {"incluye": [...], "no_incluye": [...], "referencia_fitgap": "GAP-200"},
  "estructura_organizativa": [{"area": "...", "responsabilidad": "..."}],
  "procesos_negocio": [
    {"nombre": "...", "pasos": [{"id": 1, "descripcion": "...", "reglas": "..."}]}
  ],
  "diseno_arquitectonico": {
    "modelo_datos": "texto libre",
    "tablas": [
      {"nombre": "axx_poliza", "campos": [
        {"display": "Número de póliza", "schema": "axx_numero", "tipo": "Texto",
         "requerido": True, "solo_lectura": False, "buscable": True, "notas": "..."}
      ]}
    ]
  },
  "seguridad": {
    "jerarquia_bu": "texto libre",
    "roles": [{"nombre": "...", "permisos": [
      {"tabla": "axx_poliza", "crear": "U", "leer": "BU", "escribir": "U",
       "eliminar": "N/A", "asignar": "N/A", "compartir": "N/A"}
    ]}]
  },
  "informes": [{"nombre": "...", "proposito": "...", "contenido": "...", "filtros": "..."}],
  "dashboards": [{"nombre": "...", "proposito": "...", "consumidores": "..."}],
  "almacenamiento": {"synapse": False, "datalake": False, "byod": False, "fabric": False,
                      "notas": "..."},
  "integraciones": [{"nombre": "...", "alcance": "...", "componentes": "...",
                      "formato_datos": "..."}],
  "migracion": {"datos": "...", "fuentes": "...", "herramientas": "...", "validaciones": "..."}
}
"""

from __future__ import annotations

import base64
import html as html_lib
from pathlib import Path

ASSETS_DIR = Path(__file__).parent.parent / "assets"

PENDIENTE = '<span class="pendiente">[Pendiente de definir con el cliente]</span>'


def _esc(value) -> str:
    """Escapa HTML — nunca insertar texto del usuario sin escapar."""
    if value is None:
        return PENDIENTE
    return html_lib.escape(str(value))


def _logo_b64(filename: str) -> str:
    path = ASSETS_DIR / filename
    return base64.b64encode(path.read_bytes()).decode()


def _section(number: str, title: str, body_html: str) -> str:
    return f"""
    <section class="fdd-section">
      <h2><span class="section-number">{number}</span>{_esc(title)}</h2>
      {body_html}
    </section>
    """


def _bullet_list(items: list[str] | None) -> str:
    if not items:
        return f"<p>{PENDIENTE}</p>"
    return "<ul>" + "".join(f"<li>{_esc(i)}</li>" for i in items) + "</ul>"


def _table(headers: list[str], rows: list[list]) -> str:
    if not rows:
        return f"<p>{PENDIENTE}</p>"
    thead = "".join(f"<th>{_esc(h)}</th>" for h in headers)
    tbody = ""
    for row in rows:
        tbody += "<tr>" + "".join(f"<td>{_esc(c)}</td>" for c in row) + "</tr>"
    return f'<table class="fdd-table"><thead><tr>{thead}</tr></thead><tbody>{tbody}</tbody></table>'


# ---------------------------------------------------------------------------
# Secciones (1 función por sección de secciones_guia.md)
# ---------------------------------------------------------------------------

def _sec_portada(data: dict) -> str:
    gap_id = _esc(data.get("gap_id"))
    gap_nombre = _esc(data.get("gap_nombre"))
    cliente = _esc(data.get("cliente"))
    proyecto_id = data.get("proyecto_id")
    fecha = data.get("fecha")
    logo_axxon = _logo_b64("logo-axxon.png")
    return f"""
    <header class="fdd-cover">
      <div class="cover-top">
        <img class="cover-logo" src="data:image/png;base64,{logo_axxon}" alt="Axxon" />
        <div class="cover-ring" aria-hidden="true"></div>
      </div>
      <h1 class="cover-title">Documento de Diseño<br/>Funcional y Técnico</h1>
      <h2 class="cover-gap">GAP-{gap_id}<br/>gap_{gap_nombre}</h2>
      <div class="cover-meta">
        <div>
          <p class="meta-label">Presentado por:</p>
          <p class="meta-value">Axxon</p>
        </div>
        <div>
          <p class="meta-label">Presentado a:</p>
          <p class="meta-value highlight">{cliente}</p>
          <p class="meta-value highlight">Proyecto ID {_esc(proyecto_id) if proyecto_id else PENDIENTE}</p>
        </div>
      </div>
      <p class="cover-date">{_esc(fecha) if fecha else ""}</p>
    </header>
    """


def _sec_revisiones(data: dict) -> str:
    revs = data.get("revisiones") or []
    rows = [[r.get("fecha", "—"), r.get("autor") or PENDIENTE, r.get("detalle", "Creación del documento")]
            for r in revs] or [["—", data.get("autor") or PENDIENTE, "Creación del documento"]]
    return _section("2", "Lista de actualizaciones y revisiones",
                     _table(["Fecha", "Autor", "Detalle"], rows))


def _sec_introduccion(data: dict) -> str:
    texto = data.get("introduccion")
    body = f"<p>{_esc(texto)}</p>" if texto else f"<p>{PENDIENTE}</p>"
    return _section("3", "Introducción", body)


def _sec_alcance(data: dict) -> str:
    alcance = data.get("alcance") or {}
    body = "<h3>Incluye</h3>" + _bullet_list(alcance.get("incluye"))
    body += "<h3>No incluye</h3>" + _bullet_list(alcance.get("no_incluye"))
    if alcance.get("referencia_fitgap"):
        body += f'<p class="ref-note">Ver hoja de trabajo del análisis FIT-GAP, {_esc(alcance["referencia_fitgap"])}.</p>'
    return _section("4", "Alcance", body)


def _sec_estructura_organizativa(data: dict) -> str:
    areas = data.get("estructura_organizativa") or []
    rows = [[a.get("area"), a.get("responsabilidad")] for a in areas]
    return _section("5", "Estructura organizativa y responsabilidades",
                     _table(["Área", "Responsabilidad principal"], rows))


def _sec_procesos_negocio(data: dict) -> str:
    procesos = data.get("procesos_negocio") or []
    if not procesos:
        return _section("6", "Descripción de procesos de negocio", f"<p>{PENDIENTE}</p>")
    body = ""
    for proceso in procesos:
        pasos = proceso.get("pasos") or []
        rows = [[p.get("id"), p.get("descripcion"), p.get("reglas", "—")] for p in pasos]
        body += f"<h3>{_esc(proceso.get('nombre'))}</h3>"
        body += "<p class='diagram-placeholder'>[Insertar diagrama de flujo]</p>"
        body += _table(["Step ID", "Descripción", "Reglas / Ejemplos / Comentarios"], rows)
    return _section("6", "Descripción de procesos de negocio", body)


def _sec_diseno_arquitectonico(data: dict) -> str:
    diseno = data.get("diseno_arquitectonico") or {}
    body = "<h3>7.1 Requerimientos de datos (modelo conceptual)</h3>"
    body += f"<p>{_esc(diseno.get('modelo_datos')) if diseno.get('modelo_datos') else PENDIENTE}</p>"
    body += "<h3>7.2 Estructura de tablas</h3>"
    tablas = diseno.get("tablas") or []
    if not tablas:
        body += f"<p>{PENDIENTE}</p>"
    for tabla in tablas:
        body += f"<h4><code>{_esc(tabla.get('nombre'))}</code></h4>"
        campos = tabla.get("campos") or []
        rows = [
            [c.get("display"), c.get("schema"), c.get("tipo"),
             "Sí" if c.get("requerido") else "No",
             "Sí" if c.get("solo_lectura") else "No",
             "Sí" if c.get("buscable") else "No",
             c.get("notas", "—")]
            for c in campos
        ]
        body += _table(
            ["Nombre para mostrar", "Nombre de Esquema", "Tipo de campo", "Requerido",
             "Solo Lectura", "Buscable", "Notas"], rows)
    return _section("7", "Diseño de la solución arquitectónica", body)


PERMISO_LABELS = {"N/A": "Ninguno", "U": "Usuario", "BU": "Unidad de negocio",
                   "BU+": "Unidad principal e hijas", "O": "Organización"}


def _sec_seguridad(data: dict) -> str:
    seguridad = data.get("seguridad") or {}
    body = "<h3>8.1 Jerarquía de unidades de negocio</h3>"
    body += f"<p>{_esc(seguridad.get('jerarquia_bu')) if seguridad.get('jerarquia_bu') else PENDIENTE}</p>"
    body += "<h3>8.2 Roles de seguridad</h3>"
    roles = seguridad.get("roles") or []
    if not roles:
        body += f"<p>{PENDIENTE}</p>"
    for rol in roles:
        body += f"<h4>{_esc(rol.get('nombre'))}</h4>"
        permisos = rol.get("permisos") or []
        rows = [
            [p.get("tabla"), p.get("crear"), p.get("leer"), p.get("escribir"),
             p.get("eliminar"), p.get("asignar"), p.get("compartir")]
            for p in permisos
        ]
        body += _table(["Tabla", "Crear", "Leer", "Escribir", "Eliminar", "Asignar", "Compartir"], rows)
    body += ('<p class="ref-note">Niveles: N/A (ninguno), U (usuario), BU (unidad de negocio), '
             "BU+ (unidad principal e hijas), O (organización).</p>")
    return _section("8", "Requisitos de seguridad", body)


def _sec_informes(data: dict) -> str:
    informes = data.get("informes") or []
    body = ""
    for i, inf in enumerate(informes, 1):
        body += f"<h3>Informe {i}: {_esc(inf.get('nombre'))}</h3>"
        body += _table(["Campo", "Detalle"], [
            ["Propósito", inf.get("proposito", "—")],
            ["Contenido", inf.get("contenido", "—")],
            ["Filtros", inf.get("filtros", "—")],
            ["Parámetros", inf.get("parametros", "—")],
            ["Vista", inf.get("vista", "—")],
        ])
    if not informes:
        body = f"<p>{PENDIENTE}</p>"
    return _section("9", "Informes (Reportes)", body)


def _sec_dashboards(data: dict) -> str:
    dashboards = data.get("dashboards") or []
    rows = [[d.get("nombre"), d.get("proposito"), d.get("contenido", "—"),
             d.get("consumidores", "—"), d.get("datos_requeridos", "—"), d.get("reportes", "—")]
            for d in dashboards]
    return _section("10", "Tableros (Dashboards)",
                     _table(["Nombre del Tablero", "Propósito", "Contenido", "Consumidores",
                             "Datos requeridos", "Reportes"], rows))


def _sec_almacenamiento(data: dict) -> str:
    a = data.get("almacenamiento") or {}
    rows = [
        ["Azure Synapse Link", "Sí" if a.get("synapse") else "No"],
        ["Azure Data Lake", "Sí" if a.get("datalake") else "No"],
        ["BYOD (Bring Your Own Database)", "Sí" if a.get("byod") else "No"],
        ["Microsoft Fabric", "Sí" if a.get("fabric") else "No"],
    ]
    body = _table(["Componente", "En uso"], rows)
    if a.get("notas"):
        body += f"<p>{_esc(a['notas'])}</p>"
    return _section("11", "Estrategia de almacenamiento de datos", body)


def _sec_integracion(data: dict) -> str:
    integraciones = data.get("integraciones") or []
    body = ""
    for integ in integraciones:
        body += f"<h3>{_esc(integ.get('nombre'))}</h3>"
        body += "<p class='diagram-placeholder'>[Insertar diagrama de arquitectura de integración]</p>"
        body += _table(["Campo", "Detalle"], [
            ["Alcance", integ.get("alcance", "—")],
            ["Componentes", integ.get("componentes", "—")],
            ["Estructura de datos", integ.get("formato_datos", "—")],
            ["Logging y manejo de errores", integ.get("logging", "—")],
        ])
    if not integraciones:
        body = f"<p>{PENDIENTE}</p>"
    return _section("12", "Integración", body)


def _sec_migracion(data: dict) -> str:
    m = data.get("migracion") or {}
    rows = [
        ["Datos a migrar", m.get("datos", "—")],
        ["Fuentes y formato", m.get("fuentes", "—")],
        ["Herramientas", m.get("herramientas", "—")],
        ["Validaciones", m.get("validaciones", "—")],
        ["Estrategia de pruebas", m.get("pruebas", "—")],
        ["Criterios de éxito / contingencia", m.get("criterios_exito", "—")],
    ]
    return _section("13", "Migración", _table(["Campo", "Detalle"], rows))


# ---------------------------------------------------------------------------
# Render principal
# ---------------------------------------------------------------------------

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&display=swap');

:root {
  /* Paleta "Axxon 2025" — misma extraída del theme del template PPTX de Kickoff Brief,
     no la del template Word original del FDD (esa era #1E4BF0/#1F3864 + Poppins). */
  --axx-blue: #000FC4;    /* accent1 */
  --axx-navy: #002060;    /* dk2 */
  --axx-bg: #FFFFFF;
  --axx-text: #0C0C0C;    /* dk1 */
  --axx-muted: #6B6B6B;
  --axx-border: #E0E0E0;
}
* { box-sizing: border-box; }
body {
  font-family: 'Segoe UI', sans-serif;
  color: var(--axx-text);
  background: var(--axx-bg);
  margin: 0;
  line-height: 1.6;
}
.fdd-doc { max-width: 880px; margin: 0 auto; padding: 0 32px 64px; }

.fdd-cover {
  min-height: 900px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 48px 0;
  position: relative;
}
.cover-top { display: flex; justify-content: space-between; align-items: flex-start; }
.cover-logo { height: 32px; }
.cover-ring {
  width: 90px; height: 90px; border-radius: 50%;
  border: 14px solid var(--axx-blue);
}
.cover-title {
  font-family: 'Bebas Neue', sans-serif; font-weight: 400; letter-spacing: 0.5px;
  color: var(--axx-blue); text-transform: uppercase;
  font-size: 52px; line-height: 1.1; margin: 64px 0 32px;
}
.cover-gap {
  font-family: 'Bebas Neue', sans-serif; font-weight: 400; letter-spacing: 0.5px;
  color: var(--axx-blue); text-transform: uppercase;
  font-size: 34px; line-height: 1.2; margin: 0 0 96px;
}
.cover-meta { display: flex; margin-bottom: 24px; }
.cover-meta > div { margin-right: 64px; }
.meta-label { font-weight: 600; margin: 0 0 4px; }
.meta-value { margin: 0 0 4px; }
.meta-value.highlight { background: #FFF176; display: inline-block; padding: 2px 8px; }
.cover-date { color: var(--axx-muted); font-size: 13px; }

.fdd-section { margin: 48px 0; page-break-inside: avoid; }
.fdd-section h2 {
  font-family: 'Bebas Neue', sans-serif; font-weight: 400; letter-spacing: 0.5px;
  color: var(--axx-navy); text-transform: uppercase; font-size: 26px;
  border-bottom: 3px solid var(--axx-blue); padding-bottom: 8px; margin-bottom: 16px;
}
.section-number {
  display: inline-block; background: var(--axx-blue); color: white;
  width: 28px; height: 28px; border-radius: 50%; text-align: center;
  line-height: 28px; font-size: 14px; margin-right: 10px;
}
.fdd-section h3 { color: var(--axx-navy); font-weight: 600; font-size: 17px; margin: 24px 0 8px; }
.fdd-section h4 { color: var(--axx-navy); font-weight: 600; font-size: 15px; margin: 16px 0 8px; }
.fdd-section p { margin: 8px 0; }
.fdd-section ul { margin: 8px 0; padding-left: 24px; }

.fdd-table { width: 100%; border-collapse: collapse; margin: 12px 0 24px; font-size: 14px; }
.fdd-table th {
  background: var(--axx-navy); color: white; text-align: left;
  padding: 8px 12px; font-weight: 600;
}
.fdd-table td { padding: 8px 12px; border-bottom: 1px solid var(--axx-border); }
.fdd-table tr:nth-child(even) td { background: #F7F8FC; }

.pendiente { color: #B8860B; font-style: italic; }
.diagram-placeholder {
  color: var(--axx-muted); font-style: italic; border: 1px dashed var(--axx-border);
  padding: 16px; text-align: center; border-radius: 4px;
}
.ref-note { color: var(--axx-muted); font-size: 13px; }
code { background: #F0F0F0; padding: 2px 6px; border-radius: 3px; font-size: 13px; }

.fdd-footer {
  display: flex; justify-content: space-between; align-items: center;
  margin-top: 64px; padding-top: 24px; border-top: 1px solid var(--axx-border);
}
.fdd-footer img { height: 20px; }
.fdd-footer .url { color: var(--axx-muted); font-size: 12px; }

@media print {
  .fdd-section { page-break-before: auto; }
}
"""


def render_fdd(data: dict) -> str:
    for required in ("gap_id", "gap_nombre", "cliente"):
        if not data.get(required):
            raise ValueError(f"Falta '{required}' — es obligatorio, no se genera el FDD sin esto.")

    logo_ed = _logo_b64("logo-evolucion-digital.png")

    sections = "".join([
        _sec_revisiones(data),
        _sec_introduccion(data),
        _sec_alcance(data),
        _sec_estructura_organizativa(data),
        _sec_procesos_negocio(data),
        _sec_diseno_arquitectonico(data),
        _sec_seguridad(data),
        _sec_informes(data),
        _sec_dashboards(data),
        _sec_almacenamiento(data),
        _sec_integracion(data),
        _sec_migracion(data),
    ])

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8" />
<title>FDD GAP-{_esc(data.get('gap_id'))} — {_esc(data.get('gap_nombre'))}</title>
<style>{CSS}</style>
</head>
<body>
<div class="fdd-doc">
  {_sec_portada(data)}
  {sections}
  <footer class="fdd-footer">
    <img src="data:image/png;base64,{logo_ed}" alt="Evolución Digital" />
    <span class="url">www.axxonconsulting.com</span>
  </footer>
</div>
</body>
</html>"""


def save(html_content: str, path: str) -> None:
    Path(path).write_text(html_content, encoding="utf-8")
