---
name: fdd-builder
description: Genera un Documento de Diseño Funcional (FDD) en Word (.docx) para un GAP de Dynamics 365 / Power Platform, a partir de Historias de Usuario ya refinadas (una o varias relacionadas) o de notas/archivos del usuario, con el template de marca Axxon bundleado. Activá SIEMPRE que el usuario mencione "FDD", "Functional Design Document", "Documento de Diseño Funcional", "armar un FDD", "documentar un GAP", o adjunte notas técnicas/funcionales de un GAP pidiendo formalizarlas ("documentar este GAP", "convertir estas historias/notas en FDD"). Es independiente y de distinto propósito al Blueprint general — el FDD detalla UN GAP específico, no resume el proyecto. Mantiene EXACTAMENTE estructura, encabezados, tablas y estilos de la plantilla, completando cada sección con lo que provea el usuario y marcando explícitamente lo pendiente/ambiguo/no aplica — nunca inventa contenido.
---

# FDD Builder — Fase 1 · Axxon Dataverse Agent

Genera el Documento de Diseño Funcional (FDD) — un GAP a la vez.

Este skill convierte Historias de Usuario ya refinadas (o notas/archivos del usuario) en un
FDD profesional en Word, basado en la plantilla oficial bundleada en
`assets/Plantilla_FDD.docx`.

## Qué entrega

Un único archivo `.docx` que:

- Conserva **exactamente** la estructura, encabezados, tablas y estilos de la
  plantilla (no la reescribimos: la abrimos y la rellenamos).
- Tiene la portada con `GAP-id`, `gap_nombre`, cliente y Project ID
  correctos.
- Tiene la primera fila de la tabla de actualizaciones completada con la
  fecha de hoy, el autor, versión `1.0` y "Creación del documento".
- Tiene cada sección poblada con lo que aporten las notas, y marcas
  explícitas (`[Pendiente de definir con el cliente]`, `[VERIFICAR: ...]`,
  `No aplica para este GAP`) cuando corresponda.

## Qué necesitás del usuario

Como mínimo:

- Las notas (texto pegado en el chat o archivo adjunto: `.txt`, `.md`,
  `.docx`, `.pdf`).
- Idealmente: ID y nombre del GAP, cliente, Project ID, autor.

Si falta el ID o el nombre del GAP y el resto del contexto deja entender
que el usuario quiere generar el FDD, **no bloquees**: poné un placeholder
`[VERIFICAR: GAP id]` / `[VERIFICAR: nombre del GAP]` y avanzá.

---

## Flujo de trabajo

Seguí este orden:

### 1. Recolectar y leer las notas

- Si el usuario adjuntó archivos, leelos antes de empezar a generar.
- Si hay un PDF, extraé el texto (podés usar el skill `pdf` o
  `pdftotext`).
- Si las notas vienen en castellano informal, conservás los conceptos pero
  los traducís a español formal y técnico al volcarlos al FDD.

### 2. Identificar los datos clave de la portada

Antes de tocar el documento, hacé un parse rápido para extraer:

| Dato        | Cómo identificarlo en las notas                                  |
|-------------|------------------------------------------------------------------|
| GAP id      | "GAP-200", "GAP 045", "el gap número 17", "GAP_152"              |
| GAP nombre  | descripción corta del proceso/funcionalidad                       |
| Cliente     | razón social mencionada (si las notas no lo dicen, dejar el placeholder "Cliente X") |
| Project ID  | algún código tipo "PRU00000999"                                  |
| Autor       | nombre del usuario o consultor a cargo (si no se indica, dejar "[Nombre del autor]") |

### 3. Cargar la plantilla y trabajar sobre ella

NO reescribas la plantilla desde cero — abrila con `python-docx` y editala
en su lugar. El helper `scripts/build_fdd.py` te da las funciones útiles.

```python
import sys
sys.path.insert(0, "<RUTA_AL_SKILL>/scripts")
from build_fdd import (
    load_template, replace_cover_placeholders, add_revision_row,
    find_heading_index, find_table_by_first_row, fill_first_empty_row,
    add_table_row, clear_table_data_rows, append_paragraphs_under_heading,
    schema_name, save,
)

doc = load_template("<RUTA_AL_SKILL>/assets/Plantilla_FDD.docx")
```

### 4. Llenar las secciones

Procedé en este orden, **siempre saltando una sección con un marcador
explícito (`[Pendiente de definir con el cliente]`) antes que dejarla vacía
o inventar contenido**:

1. **Portada**: `replace_cover_placeholders(doc, gap_id=..., gap_nombre=..., cliente=..., proyecto_id=...)`.
   Solo pasá los parámetros que tengas; los que omitas conservan el valor
   actual de la plantilla.
2. **Lista de actualizaciones**: `add_revision_row(doc, autor="<nombre>")`.
3. **Introducción**: dejá el texto base; agregá párrafos solo si las notas
   aportan contexto general.
4. **Alcance**: agregar párrafos con los límites/objetivos del GAP. Si las
   notas mencionan FIT-GAP, dejar la referencia.
5. **Estructura organizativa**: departamentos, áreas, roles y su impacto.
6. **Procesos de negocio**: una subsección por proceso. Llenar la tabla de
   pasos (`Step ID | Descripción | Reglas/Ejemplos/Comentarios`).
7. **Diseño arquitectónico**:
   - Requerimientos de datos (relaciones, escalabilidad, retención).
   - Estructura de tablas (opciones a habilitar y formulario de campos),
     usando `schema_name(...)` para los nombres lógicos.
8. **Requisitos de seguridad**: jerarquía de BUs, matriz de roles
   (`Tabla | Crear | Leer | Escribir | Eliminar | Asignar | Compartir`)
   con niveles `N/A | U | BU | BU+ | O`, equipos de acceso y privilegios
   misceláneos.
9. **Informes**: por cada informe, propósito/contenido/mapeo/filtros/
   parámetros/vista.
10. **Tableros**: tabla con `Nombre | Propósito | Contenido | Consumidores |
    Datos requeridos | Reportes`.
11. **Estrategia de almacenamiento**: Synapse Link / Data Lake / BYOD /
    Fabric.
12. **Integración**: por cada integración, alcance/diseño/componentes/
    estructura/mapeo/request/response/logging/errores.
13. **Migración**: datos a migrar, fuentes, mapeo, herramientas,
    validaciones, criterios de éxito.

Para los detalles de cada sección leé `references/secciones_guia.md`.

### 5. Guardar y entregar

Nombrá el archivo de forma descriptiva y guardalo en el folder de outputs:

```python
nombre = f"FDD-GAP-{gap_id}-{gap_nombre.replace(' ', '_')}.docx"
save(doc, f"<OUTPUTS>/{nombre}")
```

Devolvé al usuario el link `computer://...` al archivo generado y un
resumen *muy breve* (qué secciones quedaron pendientes, qué cosas marcaste
con `[VERIFICAR]`).

---

## Reglas de oro (no negociables)

1. **Formato preservado**: la plantilla manda. No alteres encabezados,
   estilos de heading, ni el orden de secciones. No reemplaces tablas por
   listas o por texto plano.
2. **Completitud honesta**: si una sección no está cubierta por las notas,
   escribí literalmente `[Pendiente de definir con el cliente]`. No
   improvises contenido para "verse bien".
3. **Ambigüedad explícita**: si las notas son ambiguas, marcá la duda
   inline como `[VERIFICAR: {detalle concreto}]`. El revisor humano va a
   poder buscar esa cadena para resolver.
4. **No aplica con justificación**: si una sección claramente no aplica
   al GAP (ej. una integración pura no tiene "Migración"), escribí
   `No aplica para este GAP — {breve justificación}`.
5. **Idioma**: español formal y técnico. Conservá los términos de
   Dynamics 365 / Power Platform en su forma habitual (Lookup, Option Set,
   Business Unit, etc.).
6. **No inventar**: el FDD es un documento contractual. Solo poné en él
   información que esté en las notas o que se deduzca trivialmente
   (la fecha de hoy, una numeración secuencial de pasos, los nombres
   lógicos derivados por convención).
7. **Convenciones de nomenclatura** (usar `schema_name(...)` o aplicar a
   mano):
   - Texto/moneda/numérico: `prefijo_logicalname` (ej `axx_account`)
   - Option Set: `prefijo_<nombre>code` (ej `axx_accounttypecode`)
   - Booleano: `prefijo_is<nombre>` (ej `axx_ispartnerproject`)
   - Fecha: `prefijo_<nombre>date` (ej `axx_paymentdate`)
   - Lookup: `prefijo_<nombre>id` (ej `axx_contactid`)
   - Todo en minúsculas, sin acentos, sin espacios.

---

## Recursos del skill

- `assets/Plantilla_FDD.docx` — la plantilla. **Nunca** la modifiques en su
  lugar; siempre cargala con `load_template` y guardá el resultado en otro
  archivo.
- `scripts/build_fdd.py` — funciones para portada, tabla de revisiones,
  búsqueda de headings y tablas, inserción de párrafos, y `schema_name(...)`.
- `references/secciones_guia.md` — guía detallada por sección, con el
  índice de tablas conocidas (`doc.tables[i]`) para localizar rápido la
  tabla correcta.

---

## Casos límite y consejos prácticos

- **Notas muy breves**: aún así generá el documento. La mayor parte tendrá
  `[Pendiente de definir con el cliente]` y eso está bien — el FDD es
  iterativo.
- **Notas muy extensas**: hacé un primer pase de organización en tu cabeza
  (qué corresponde a Procesos, qué a Integración, qué a Seguridad) antes
  de empezar a editar el .docx.
- **Múltiples procesos / integraciones / informes**: cada uno necesita su
  propia subsección. Usá `Heading 2` para títulos como "Proceso 1 — Alta de
  cliente" y `Heading 3` cuando convenga subdividir.
- **Tablas adicionales**: si necesitás una tabla nueva del mismo tipo que
  una existente (p.ej., una segunda tabla de pasos para un segundo
  proceso), preferí clonar el `<w:tbl>` de la plantilla con
  `copy.deepcopy(tabla._element)` para preservar el estilo, en lugar de
  crear una con `doc.add_table` (que no hereda el formato visual).
- **Diagramas**: nunca los inventes. Donde haga falta uno, dejá un párrafo
  con `[Insertar diagrama de flujo]` o
  `[Insertar diagrama de arquitectura de integración]`.

---

## Limpieza de filas placeholder en tablas

La plantilla trae filas de ejemplo en algunas tablas — por ejemplo la tabla
de pasos arranca con `# | A completar | A completar`. Cuando vas a poblar
una tabla con datos reales, **limpiá primero esas filas** para que no
queden mezcladas con tu contenido:

```python
tabla = find_table_by_first_row(doc, ["Step ID", "Descripción"])
clear_table_data_rows(tabla)              # deja solo el header
for paso in pasos:
    add_table_row(tabla, [paso["id"], paso["desc"], paso["regla"]])
```

`fill_first_empty_row` es útil cuando el caller solo quiere completar el
primer hueco real (por ejemplo, una tabla de revisiones donde sí queremos
mantener filas previas). Para tablas de pasos, formularios de campos,
matrices de roles y dashboards, lo correcto casi siempre es
`clear_table_data_rows` + `add_table_row`.

---

## Smoke test rápido

Para verificar que la plantilla y el helper funcionan en un entorno nuevo:

```bash
pip install python-docx --break-system-packages
python scripts/build_fdd.py \
  --template assets/Plantilla_FDD.docx \
  --output /tmp/FDD-smoke.docx \
  --gap-id 200 \
  --gap-nombre "Integracion SAP" \
  --cliente "ACME" \
  --proyecto-id "PRU00000999" \
  --autor "Consultor de Prueba"
```

Si el comando termina con "FDD generado en: /tmp/FDD-smoke.docx" y el .docx
abre sin errores en Word, todo lo demás (que es python-docx aplicado a la
misma plantilla) va a funcionar.
