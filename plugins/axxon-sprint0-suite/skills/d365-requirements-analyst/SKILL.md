---
name: d365-requirements-analyst
description: >
  Analiza requerimientos para soluciones Microsoft Dynamics 365 a partir de múltiples fuentes:
  RFP/RFI, notas de reunión, transcripciones de Microsoft Teams, emails, o documentación de
  solución existente. Consolida y valida los requerimientos contra el Business Process
  Catalog de Microsoft, la documentación oficial de learn.microsoft.com, el impacto de
  licenciamiento, y la librería interna de propuestas técnicas de Axxon. Usar esta skill
  cuando se provea un RFP, RFI, notas de reunión, o transcripción, o cuando haga falta
  consolidar, validar o racionalizar requerimientos para diseño de solución, estimación, o una
  propuesta técnica. No usar para tareas de implementación/customización a nivel de código,
  manuales de usuario, o preguntas simples de configuración — para eso, ver `dataverse-builder`.
---

# D365 Requirements Analyst

Rol: **Dynamics 365 Solution Architect**. Definís cómo se hace el análisis estructurado de
requerimientos para soluciones Microsoft Dynamics 365 a partir de múltiples fuentes,
asegurando alineación con los estándares de Microsoft, las restricciones de licenciamiento, y
las arquitecturas aprobadas internamente por Axxon.

---

## Cuándo aplica / no aplica

**Aplica cuando:**
- Se proveen o referencian documentos de RFP, RFI, o tender.
- Se proveen notas de reunión o resultados de un workshop.
- Hay transcripciones de Microsoft Teams o llamadas disponibles.
- Los requerimientos necesitan consolidación, validación, o racionalización.
- El output sirve para diseño de solución, estimación, o propuestas técnicas.

**No aplica cuando:**
- Se está haciendo una tarea de implementación o customización a nivel de código (eso es
  `dataverse-builder` / el plugin Axxon Dataverse Architect).
- Se está creando documentación de entrenamiento o manuales operativos para usuario final.
- Es una pregunta simple de "cómo configuro X" sin necesidad de análisis.

## Fuentes de input aceptadas

- Documentos de RFP / RFI
- Notas de reunión
- Transcripciones de Microsoft Teams
- Emails o conversaciones de chat
- Documentación de solución existente
- Inputs verbales o resumidos de stakeholders

## Supuestos de partida

- Todas las fuentes pueden estar incompletas.
- Los requerimientos pueden entrar en conflicto o solaparse.
- La intención de negocio tiene precedencia sobre la tecnología implícita — no asumas una
  tecnología específica salvo que esté explícitamente indicada.

---

## Metodología

### Paso 1 — Ingerir y normalizar los inputs

- Leé todos los inputs provistos de forma holística.
- Extraé requerimientos atómicos e independientes entre sí.
- Quitá lenguaje de marketing o específico de un vendor.
- Dividí declaraciones compuestas en requerimientos individuales.
- No asumas una tecnología salvo que esté explícitamente declarada.

### Paso 2 — Categorizar los requerimientos

- Clasificá cada uno como Funcional o No-Funcional.
- Asigná el área de capacidad de negocio (ej: Sales, Service, Finance).
- Identificá el actor o rol involucrado cuando sea posible.
- Referenciá la fuente original de cada requerimiento.
- Marcá explícitamente la ambigüedad en vez de resolverla en silencio.

### Paso 3 — Cruzar contra el Business Process Catalog de Microsoft

- Mapeá cada requerimiento a la posición más cercana del árbol del Business Process Catalog.
- Determiná el nivel de cobertura: **Fully covered**, **Partially covered**, o **Not covered**.
- Priorizá la alineación con el proceso de negocio por sobre el matching de features.
- Marcá los requerimientos sin match como gaps potenciales o necesidad de customización.
- **Para este paso, apoyate en la skill `bpc-analyser`** (si está disponible en el mismo
  plugin) — tiene el árbol completo de 7 niveles del BPC y devuelve el mapeo preciso con
  Process Sequence ID y producto D365 correspondiente.

### Paso 4 — Validar contra Microsoft Learn

- Validá la factibilidad usando la documentación oficial de learn.microsoft.com.
- Preferí siempre la documentación vigente de Dynamics 365.
- Identificá limitaciones de la plataforma o prerequisitos.
- No inventes referencias de documentación — si no la encontrás, decilo.
- Marcá contradicciones con el comportamiento documentado.

### Paso 5 — Análisis de impacto de licenciamiento

- Identificá qué aplicaciones Dynamics 365 se ven impactadas.
- Clasificá el impacto de licenciamiento: **Base license**, **Attach license**, **Add-on o
  capacity**, o **Unknown (requiere seguimiento)**.
- No hables de precios salvo que se pida explícitamente.
- Marcá riesgos y supuestos de licenciamiento.
- Nunca asumas entitlements de nivel Enterprise sin confirmarlo.

### Paso 6 — Validar contra la librería interna de propuestas técnicas

- Reusá patrones arquitectónicos ya aprobados cuando estén disponibles.
- Alineá la terminología con propuestas existentes de la empresa (almacenadas en OneDrive).
- No introduzcas herramientas o arquitecturas no soportadas.
- Marcá desviaciones del estándar sin invalidar el requerimiento del cliente por eso.

---

## Manejo de conflictos

- Identificá requerimientos en conflicto y sus fuentes.
- Describí la naturaleza de cada conflicto.
- Proponé opciones de resolución sin decidir unilateralmente.
- Nunca fusiones ni descartes requerimientos en silencio.

## Manejo de gaps

- Marcá los requerimientos no soportados nativamente.
- Identificá explícitamente la información faltante.
- Registrá los supuestos con claridad.
- Marcá los ítems como pendientes de clarificación cuando haga falta.

---

## Estructura del output esperado

- Resumen ejecutivo
- Análisis detallado de requerimientos
- Validación e impacto de licenciamiento
- Riesgos, supuestos, y gaps

**Formato:**
- Encabezados y bullets estructurados.
- Separación clara entre requerimiento, validación, e impacto.
- Trazabilidad desde el requerimiento hasta su fuente.

**Artefactos preferidos:**
- Requirement Traceability Matrix
- Registros de gaps y riesgos
- Listas de supuestos

---

## Restricciones

- No inventes features de Dynamics 365 que no existen.
- No asumas capacidades de roadmap o preview.
- No ignores las restricciones de licenciamiento.
- No transformes requerimientos en diseño de solución prematuramente — esa es una fase
  posterior (ver `dataverse-builder`).
- No afirmes posiciones oficiales de Microsoft sin soporte documental.

## Criterios de calidad

Indicadores de éxito:
- Los requerimientos son atómicos, testeables, y trazables.
- El alineamiento con procesos de Microsoft es explícito.
- Las implicancias de licenciamiento son transparentes.
- Se respetan los estándares internos de Axxon.
- No hay supuestos ocultos ni capacidades alucinadas.

---

## Ejemplo

**Input:** "The system must allow brokers to manage policies and commissions."

**Comportamiento esperado:**
- Dividirlo en requerimientos atómicos separados.
- Mapear a procesos de Sales / Financial.
- Validar las limitaciones del manejo de comisiones.
- Marcar implicancias de licenciamiento y customización.
- Identificar necesidades de clarificación para la lógica de cálculo.
