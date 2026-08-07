#!/usr/bin/env python3
"""
build_fdd.py - Utilidades para llenar la plantilla FDD (Documento de Diseño
Funcional) preservando estructura, estilos y tablas.

Uso típico:

    from build_fdd import (
        load_template, replace_cover_placeholders, add_revision_row,
        find_heading_index, get_section_paragraph_indices, fill_first_empty_row,
        clear_table_data_rows, add_table_row, find_table_by_first_row,
        insert_paragraph_after, append_paragraphs_under_heading, schema_name, save,
    )

    doc = load_template("assets/Plantilla_FDD.docx")
    replace_cover_placeholders(doc, gap_id="200", gap_nombre="Integracion SAP",
                               cliente="ACME", proyecto_id="PRU00000999")
    add_revision_row(doc, autor="<nombre del consultor>")
    # ... resto del llenado por sección ...
    save(doc, "outputs/FDD-GAP-200-IntegracionSAP.docx")
"""

from copy import deepcopy
from datetime import date
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn

W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


# ---------- Carga / guardado ----------

def load_template(template_path):
    """Abre la plantilla FDD y devuelve un objeto Document de python-docx."""
    return Document(str(template_path))


def save(doc, output_path):
    """Guarda el Document en la ruta destino, creando la carpeta si hace falta."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out))


# ---------- Portada (texto en text boxes) ----------

def replace_cover_placeholders(doc, *, gap_id=None, gap_nombre=None,
                               cliente=None, proyecto_id=None):
    """
    Reemplaza los placeholders de la portada de la plantilla. La portada vive
    dentro de text boxes (txbxContent), por lo que estos textos no son visibles
    a través de doc.paragraphs y deben editarse en el XML.

    Placeholders en la plantilla neutralizada (Axxon):
      - "[ID]"              -> reemplazar por gap_id (lo que va después de "GAP-")
      - "[Nombre del GAP]"  -> reemplazar por gap_nombre (lo que va después de "gap_")
      - "Cliente X"         -> reemplazar por cliente
      - "[Project ID]"      -> reemplazar por proyecto_id

    Solo se aplican los reemplazos cuyos parámetros NO sean None, así se puede
    actualizar parcialmente (por ejemplo, mantener "Cliente X" como recordatorio
    de que falta ese dato en vez de dejarlo vacío).
    """
    replacements = {}
    if gap_id is not None:
        replacements["[ID]"] = str(gap_id)
    if gap_nombre is not None:
        replacements["[Nombre del GAP]"] = gap_nombre
    if cliente is not None:
        replacements["Cliente X"] = cliente
    if proyecto_id is not None:
        replacements["[Project ID]"] = proyecto_id

    if not replacements:
        return

    for txbx in doc.element.iter(W_NS + "txbxContent"):
        for t in txbx.iter(W_NS + "t"):
            if t.text:
                for old, new in replacements.items():
                    if old in t.text:
                        t.text = t.text.replace(old, new)


# ---------- Lista de actualizaciones / Revisiones ----------

def add_revision_row(doc, *, fecha=None, autor="",
                     version="1.0", detalles="Creación del documento"):
    """
    Completa la primera fila (después del header) de la tabla
    'Lista de actualizaciones' (doc.tables[0]) con los datos de creación
    del nuevo FDD. Si esa fila tiene algún contenido de ejemplo, lo
    sobrescribe — esto es lo correcto: cada FDD nuevo nace en la fecha y
    autor que se le pasa.

    Si por alguna razón la tabla solo tiene header, agrega una fila nueva.
    """
    if fecha is None:
        fecha = date.today().strftime("%d/%m/%Y")
    table = doc.tables[0]
    values = [fecha, autor, version, detalles]
    if len(table.rows) >= 2:
        row = table.rows[1]
        for i, v in enumerate(values):
            if i < len(row.cells):
                row.cells[i].text = str(v)
    else:
        add_table_row(table, values)


# ---------- Búsqueda y manipulación de secciones ----------

def find_heading_index(doc, heading_text, level=None):
    """
    Devuelve el índice (en doc.paragraphs) del primer heading cuyo texto
    coincida con heading_text (case-insensitive, ignorando espacios). Si se
    pasa level, restringe a 'Heading {level}'. Devuelve None si no encuentra.
    """
    target = heading_text.strip().lower()
    for i, p in enumerate(doc.paragraphs):
        style = p.style.name if p.style else ""
        if not style.startswith("Heading"):
            continue
        if level is not None and style != f"Heading {level}":
            continue
        if p.text.strip().lower() == target:
            return i
    return None


def get_section_paragraph_indices(doc, heading_text):
    """
    Devuelve los índices de párrafos pertenecientes a la sección que arranca
    con heading_text, hasta (sin incluir) el siguiente heading del mismo o
    menor nivel. Útil para revisar/limpiar el contenido textual de una sección.
    """
    start = find_heading_index(doc, heading_text)
    if start is None:
        return []
    start_style = doc.paragraphs[start].style.name
    try:
        start_level = int(start_style.split()[-1])
    except (ValueError, IndexError):
        start_level = 1
    indices = []
    for i in range(start + 1, len(doc.paragraphs)):
        s = doc.paragraphs[i].style.name
        if s.startswith("Heading "):
            try:
                lvl = int(s.split()[-1])
            except ValueError:
                lvl = 1
            if lvl <= start_level:
                break
        indices.append(i)
    return indices


def insert_paragraph_after(paragraph, text="", style=None):
    """
    Inserta un nuevo párrafo después del párrafo dado y devuelve el nuevo
    objeto Paragraph. Hereda las propiedades del párrafo de referencia salvo
    que se pase 'style' (nombre del estilo, p.ej. 'Normal', 'List Paragraph').
    """
    new_p_el = deepcopy(paragraph._element)
    paragraph._element.addnext(new_p_el)
    # Limpiar runs del nuevo párrafo
    for r in list(new_p_el.findall(qn("w:r"))):
        new_p_el.remove(r)

    new_para = paragraph.__class__(new_p_el, paragraph._parent)
    if text:
        new_para.add_run(text)
    if style is not None:
        try:
            new_para.style = paragraph.part.document.styles[style]
        except Exception:
            try:
                new_para.style = style
            except Exception:
                pass
    return new_para


def append_paragraphs_under_heading(doc, heading_text, paragraphs):
    """
    Inserta una lista de párrafos inmediatamente después del heading indicado.

    paragraphs: list of dict with keys:
        - 'text'  (str): contenido del párrafo
        - 'style' (str, opcional): nombre del estilo. Por defecto 'Normal'.

    Importante: NO elimina el contenido existente. Si querés reemplazar el
    texto base de la plantilla, primero leelo con get_section_paragraph_indices
    y eliminá los párrafos que correspondan antes de insertar los nuevos.
    """
    idx = find_heading_index(doc, heading_text)
    if idx is None:
        raise ValueError(f"Heading no encontrado: {heading_text!r}")
    anchor = doc.paragraphs[idx]
    # Mantener orden: insertamos en orden inverso justo después del heading
    for item in reversed(paragraphs):
        insert_paragraph_after(anchor,
                                text=item.get("text", ""),
                                style=item.get("style", "Normal"))


# ---------- Tablas ----------

def find_table_by_first_row(doc, expected_first_row):
    """
    Busca la primera tabla cuyo primer row contiene (al inicio) las celdas
    pasadas (case-insensitive, comparando texto stripeado). Devuelve la tabla
    o None.
    """
    target = [c.strip().lower() for c in expected_first_row]
    for t in doc.tables:
        if not t.rows:
            continue
        first = [c.text.strip().lower() for c in t.rows[0].cells]
        if first[: len(target)] == target:
            return t
    return None


def add_table_row(table, values):
    """Agrega una fila al final de la tabla con los valores indicados."""
    row = table.add_row()
    for i, v in enumerate(values):
        if i < len(row.cells):
            row.cells[i].text = str(v)
    return row


def fill_first_empty_row(table, values):
    """
    Completa la primera fila VACÍA (después del header) de la tabla. Si no
    hay fila vacía disponible, agrega una nueva al final.
    """
    for row in table.rows[1:]:
        cells = [c.text.strip() for c in row.cells]
        if all(not c for c in cells):
            for i, v in enumerate(values):
                if i < len(row.cells):
                    row.cells[i].text = str(v)
            return row
    return add_table_row(table, values)


def clear_table_data_rows(table, keep_header=True):
    """
    Elimina todas las filas excepto la primera (header). Útil cuando hay que
    reemplazar contenido de ejemplo de la plantilla por datos reales.
    """
    rows = list(table.rows)
    start = 1 if keep_header else 0
    for row in rows[start:]:
        row._element.getparent().remove(row._element)


# ---------- Convenciones de nomenclatura de campos ----------

def schema_name(prefix, display_name, field_type):
    """
    Aplica las convenciones de nomenclatura de la plantilla FDD:

      - Texto / moneda / numéricos        -> {prefix}_{nombre}
      - Option Set / MultiSelect          -> {prefix}_{nombre}code
      - Booleano (Two Options)            -> {prefix}_is{nombre}
      - Fecha                             -> {prefix}_{nombre}date
      - Lookup                            -> {prefix}_{nombre}id

    El nombre se normaliza a minúsculas, sin espacios ni acentos.

    Ejemplos (prefijo estándar de Axxon: "axx"):
        schema_name("axx", "Account", "text")         -> "axx_account"
        schema_name("axx", "Account Type", "optionset") -> "axx_accounttypecode"
        schema_name("axx", "Partner Project", "boolean") -> "axx_ispartnerproject"
        schema_name("axx", "Payment", "date")          -> "axx_paymentdate"
        schema_name("axx", "Contact", "lookup")        -> "axx_contactid"
    """
    import re
    import unicodedata

    base = unicodedata.normalize("NFKD", display_name)
    base = "".join(c for c in base if not unicodedata.combining(c))
    base = re.sub(r"[^a-zA-Z0-9]+", "", base).lower()

    t = field_type.lower()
    if t in ("optionset", "option set", "choice", "multiselect",
             "multi-select", "multiselect option set"):
        return f"{prefix}_{base}code"
    if t in ("boolean", "two options", "twooptions", "bit", "bool"):
        return f"{prefix}_is{base}" if not base.startswith("is") else f"{prefix}_{base}"
    if t in ("date", "datetime", "fecha", "fecha y hora"):
        return f"{prefix}_{base}date" if not base.endswith("date") else f"{prefix}_{base}"
    if t in ("lookup", "búsqueda", "busqueda", "customer"):
        return f"{prefix}_{base}id" if not base.endswith("id") else f"{prefix}_{base}"
    return f"{prefix}_{base}"


# ---------- CLI rápido para smoke tests ----------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Smoke test del helper FDD")
    parser.add_argument("--template", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--gap-id")
    parser.add_argument("--gap-nombre")
    parser.add_argument("--cliente")
    parser.add_argument("--proyecto-id")
    parser.add_argument("--autor", default="")
    args = parser.parse_args()

    doc = load_template(args.template)
    replace_cover_placeholders(doc,
                                gap_id=args.gap_id,
                                gap_nombre=args.gap_nombre,
                                cliente=args.cliente,
                                proyecto_id=args.proyecto_id)
    add_revision_row(doc, autor=args.autor)
    save(doc, args.output)
    print(f"FDD generado en: {args.output}")
