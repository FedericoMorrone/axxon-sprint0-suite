# Guía de llenado por sección — FDD

Este documento describe, sección por sección, cómo extraer y volcar la
información de las notas del usuario al FDD. Está pensado para leerse en
conjunto con `SKILL.md` y `scripts/build_fdd.py`.

> Regla transversal: si las notas no cubren una sección, escribir
> "[Pendiente de definir con el cliente]". Si algo es ambiguo, marcarlo como
> "[VERIFICAR: {detalle concreto}]". Si una sección no aplica al GAP, escribir
> "No aplica para este GAP" con una breve justificación. Nunca inventar datos.

---

## 1. Portada

Reemplazar los placeholders del cover (text boxes) usando
`replace_cover_placeholders(...)`:

| Placeholder en plantilla | Significado            | Origen en las notas                           |
|--------------------------|------------------------|-----------------------------------------------|
| `[ID]` (después de `GAP-`) | ID del GAP             | "GAP-200", "gap 045", "el GAP número ..."     |
| `[Nombre del GAP]`       | Nombre del GAP          | nombre descriptivo del proceso/funcionalidad  |
| `Cliente X`              | Cliente                 | razón social/empresa cliente (si difiere)     |
| `[Project ID]`           | Proyecto ID             | si las notas lo especifican                   |

Si las notas no mencionan cliente o Proyecto ID, **dejar el valor original**
de la plantilla (no pasar el parámetro a la función).

## 2. Lista de actualizaciones y revisiones

Tabla 0 (`doc.tables[0]`). Completar la primera fila vacía con
`add_revision_row(doc, autor="<nombre>")`. Por defecto:

- Fecha: hoy (DD/MM/AAAA)
- Versión: `1.0`
- Detalles: `Creación del documento`

Nombre del autor: usar el nombre que aparezca en las notas del usuario, o el
nombre del consultor que esté haciendo la solicitud. Si ninguno está
disponible, dejar el placeholder "[Nombre del autor]" — nunca inventar un
nombre.

## 3. Introducción

Mantener intacto el texto base de la plantilla. Solo agregar párrafos
adicionales si las notas aportan contexto general relevante (alcance global,
encuadre del programa, etc.). Insertar con
`append_paragraphs_under_heading(doc, "Introducción", [...])`.

## 4. Alcance

Tres cosas:

1. Mantener el listado base de la plantilla (los bullets que enumeran qué
   incluye el FDD).
2. Agregar uno o más párrafos describiendo límites y objetivos concretos del
   GAP según las notas (qué entra, qué queda fuera).
3. Si las notas mencionan un análisis FIT-GAP, dejar la referencia explícita
   (por ejemplo: "Ver hoja de trabajo del análisis FIT-GAP, GAP-{id}.").

## 5. Estructura organizativa y responsabilidades

De las notas extraer:

- Departamentos/áreas implicados (Ventas, Logística, Finanzas, etc.).
- Roles funcionales (Supervisor, Operador, Aprobador, etc.).
- Cómo participa cada uno en el proceso (quién crea, quién aprueba, quién
  consulta).
- Impacto en seguridad y workflows (esto se va a referenciar luego en la
  sección de Roles de seguridad).

Formato sugerido: párrafos en prosa por área + un bullet list final con la
matriz "Área — Responsabilidad principal".

## 6. Descripción de procesos de negocio

Por cada proceso identificado en las notas crear una subsección
(`Heading 2`). Para cada proceso completar la tabla de pasos (la plantilla
trae una tabla modelo `Step ID | Descripción | Reglas/Ejemplos/Comentarios`,
es la `find_table_by_first_row(doc, ["Step ID", "Descripción", "Reglas/Ejemplos/Comentarios"])`).

Reglas:

- Numerar los pasos en orden secuencial (1, 2, 3, ...).
- Si las notas describen un flujo, traducirlo a pasos discretos.
- Donde aplique un diagrama de flujo, dejar el placeholder
  `[Insertar diagrama de flujo]` como párrafo previo a la tabla.
- Cada nuevo proceso normalmente requiere DUPLICAR la tabla modelo. Para
  hacerlo: clonar el `<w:tbl>` del XML usando `copy.deepcopy(tabla._element)`
  e insertarlo donde corresponda. Si esto se vuelve frágil, una alternativa
  válida es llenar la tabla existente con el primer proceso y agregar las
  tablas adicionales como objeto `doc.add_table(...)` aplicando estilo
  `'Table Grid'` (pero conservar headers idénticos a la plantilla).

## 7. Diseño de la solución arquitectónica

### 7.1 Requerimientos de datos (modelo conceptual)

Documentar:

- Entidades involucradas y sus relaciones (1:N, N:N).
- Consideraciones de escalabilidad y rendimiento.
- Índices recomendados.
- Estrategia de retención y archivado de datos.

### 7.2 Estructura de tablas

Para cada tabla/entidad mencionada en las notas:

1. **Opciones habilitar/deshabilitar** — la plantilla trae una tabla modelo
   con 21 filas con `Habilitar/Deshabilitar` por opción. Marcar `Habilitar`
   o `Deshabilitar` según las notas.
2. **Formulario de campos** — completar la tabla con columnas:
   `Nombre para mostrar | Nombre de Esquema | Tipo de campo | Requerido |
    Solo Lectura | Buscable | Notas`
   (es la `find_table_by_first_row(doc, ["Nombre para mostrar", "Nombre de Esquema", ...])`).

### Convenciones de nomenclatura (usar `schema_name(...)`)

| Tipo                       | Convención                | Ejemplo                  |
|----------------------------|---------------------------|--------------------------|
| Texto / moneda / numérico  | `{prefijo}_{nombre}`      | `axx_account`            |
| Option Set                 | `{prefijo}_{nombre}code`  | `axx_accounttypecode`    |
| Booleano                   | `{prefijo}_is{nombre}`    | `axx_ispartnerproject`   |
| Fecha                      | `{prefijo}_{nombre}date`  | `axx_paymentdate`        |
| Lookup                     | `{prefijo}_{nombre}id`    | `axx_contactid`          |

Todo en minúsculas, sin acentos, sin espacios. Prefijo por defecto: `new`
(salvo que las notas indiquen un publisher distinto).

## 8. Requisitos de seguridad

### 8.1 Jerarquía de unidades de negocio

Describir en prosa o lista la jerarquía de BUs según las notas. Si no hay
datos, dejar `[Pendiente de definir con el cliente]` debajo del placeholder
existente.

### 8.2 Roles de seguridad

Por cada rol mencionado completar la tabla
`Tabla | Crear | Leer | Escribir | Eliminar | Asignar | Compartir`
(la `find_table_by_first_row(doc, ["Tabla", ...])`). Niveles válidos:

| Nivel                          | Abreviatura |
|--------------------------------|-------------|
| Ninguno seleccionado            | `N/A`       |
| Usuario                         | `U`         |
| Unidad de negocio               | `BU`        |
| Unidad principal e hijas        | `BU+`       |
| Organización                    | `O`         |

Incluir también los equipos de acceso (Access Teams) y privilegios
misceláneos (Edición Masiva, Combinar, Auditoría, etc.) si las notas los
mencionan.

## 9. Informes (Reportes)

Por cada informe en las notas, completar:

- **Propósito**
- **Contenido** (métricas, KPIs, campos clave)
- **Mapeo de campos** (qué campo del modelo alimenta qué dato)
- **Filtros** disponibles
- **Parámetros** configurables al ejecutar el reporte
- **Vista** (tabla, gráfico, matriz)

Estructura: usar el patrón `Informe x` que ya está en la plantilla y
duplicarlo por cada informe.

## 10. Tableros (Dashboards)

Tabla con columnas:
`Nombre del Tablero | Propósito | Contenido | Consumidores | Datos requeridos | Reportes`
(la `find_table_by_first_row(doc, ["Nombre del Tablero", ...])`).

Una fila por dashboard.

## 11. Estrategia de almacenamiento de datos

Documentar uso (sí/no/futuro) de:

- Azure Synapse Link
- Azure Data Lake
- BYOD (Bring Your Own Database)
- Microsoft Fabric

Incluir frecuencia de actualización, fuentes y volumen estimado si las notas
lo cubren.

## 12. Integración

Por cada integración mencionada:

- **Alcance** (sistemas origen y destino, tipo de datos, frecuencia,
  bidireccional o no).
- **Diseño de interfaz** (diagrama de arquitectura — placeholder
  `[Insertar diagrama de arquitectura de integración]`).
- **Componentes** (conectores, colas, API gateway, ETL, middleware).
- **Estructura de datos** (JSON, XML, CSV, etc.).
- **Mapeo de campos** (idealmente en tabla origen→destino).
- **Formato de Request / Response** (con ejemplo si las notas lo proveen).
- **Logging y manejo de errores**.

## 13. Migración

Documentar:

- Datos a migrar: configuración, maestros, históricos.
- Fuentes y formato original.
- Mapeo de campos origen → destino.
- Herramientas (Data Import, Dataflows, KingswaySoft, Scribe, etc.).
- Validaciones pre y post migración.
- Estrategia de pruebas.
- Criterios de éxito y plan de contingencia.

---

## Tablas conocidas en la plantilla (índice rápido)

Para localizar las tablas con `find_table_by_first_row(...)` o con
`doc.tables[i]`:

| Idx | Encabezados                                                      | Sección                          |
|-----|------------------------------------------------------------------|----------------------------------|
| 0   | `Fecha, Autor, Versión, Detalles`                                 | Lista de actualizaciones         |
| 1   | `Fecha, Versión, Responsable, observaciones`                       | Revisiones                       |
| 2   | `Step ID, Descripción, Reglas/Ejemplos/Comentarios`                | Pasos de proceso (modelo)        |
| 3   | `Opción, Comentarios`                                              | Opciones de tabla (a habilitar)  |
| 4   | `Opción, Comentarios`                                              | Opciones habilitar/deshabilitar  |
| 5   | `Opción, Comentarios`                                              | Propiedades de campo (referencia)|
| 6   | `Opción, Comentarios`                                              | Tipos de datos (referencia)      |
| 7   | `Opción, Comentarios`                                              | Convenciones de nomenclatura     |
| 8   | `Nombre para Mostrar, Nombre Lógico, Tipo, Requerido, ...`         | Campos comunes (referencia)      |
| 9   | `Opción, Habilitar/Deshabilitar, Comentarios`                      | Tabla/Entidad N — opciones       |
| 10  | `Nombre para mostrar, Nombre de Esquema, ...`                      | Formulario — campos personalizados |
| 11  | `Nivel de Acceso, Abreviatura`                                     | Niveles de acceso (referencia)   |
| 12  | `Nombre del Equipo, Abreviatura`                                   | Equipos de acceso                 |
| 13  | `Tabla, Crear, Leer, Escribir, Eliminar, Asignar, Compartir`       | Matriz de permisos por rol        |
| 14  | `Nombre del Tablero, Propósito, Contenido, ...`                    | Tableros                          |

> Las tablas 3-9 y 11 son fundamentalmente **referencia** para el lector del
> FDD; normalmente no necesitan modificarse. Las tablas 0, 2, 9, 10, 13 y 14
> son las que típicamente vas a poblar.
