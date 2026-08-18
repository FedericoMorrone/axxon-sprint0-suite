---
name: fdd-builder
description: Genera un Documento de Diseño Funcional (FDD) como HTML autocontenido (marca Axxon 2025 — Bebas Neue + Segoe UI, azul #000FC4, navy #002060) para un GAP de Dynamics 365 / Power Platform, a partir de Historias de Usuario ya refinadas (una o varias relacionadas) o de notas/archivos del usuario. Activá SIEMPRE que el usuario mencione "FDD", "Functional Design Document", "Documento de Diseño Funcional", "armar un FDD", "documentar un GAP", o adjunte notas técnicas/funcionales de un GAP pidiendo formalizarlas ("documentar este GAP", "convertir estas historias/notas en FDD"). Es independiente y de distinto propósito al Blueprint general — el FDD detalla UN GAP específico, no resume el proyecto. Completa cada sección con lo que provea el usuario y marca explícitamente lo pendiente/ambiguo/no aplica — nunca inventa contenido.
---

# FDD Builder — Fase 1 · Axxon Dataverse Agent

Genera el Documento de Diseño Funcional (FDD) — un GAP a la vez.

Convierte Historias de Usuario ya refinadas (o notas/archivos del usuario) en un FDD
profesional, entregado como **un solo archivo HTML autocontenido** (CSS y logos embebidos —
se abre en cualquier navegador sin dependencias, y se puede imprimir a PDF desde ahí).

> **Cambio de formato**: versiones anteriores de esta skill generaban `.docx` rellenando una
> plantilla Word real de Axxon. Esa plantilla queda como referencia de diseño en
> `assets/Plantilla_FDD_legacy_reference.docx`, pero ya no se usa para generar — el output
> actual siempre es HTML, vía `scripts/build_fdd_html.py`.

## Qué entrega

Un archivo `.html` que:

- Respeta la identidad visual **Axxon 2025** (la misma paleta del template PPTX de
  `kickoff-brief`, Fase 0 — no la del template Word original del FDD, que era distinta):
  tipografía **Bebas Neue** (títulos grandes — portada y encabezados de sección) + **Segoe
  UI** (cuerpo, tablas, subtítulos), azul de marca `#000FC4`, navy `#002060`.
- Trae los dos logos reales embebidos (`assets/logo-axxon.png`,
  `assets/logo-evolucion-digital.png`) en base64 — el archivo funciona standalone, sin
  depender de que las imágenes estén disponibles por separado.
- Cubre las 13 secciones estándar del FDD (ver `references/secciones_guia.md`): portada,
  revisiones, introducción, alcance, estructura organizativa, procesos de negocio, diseño
  arquitectónico, seguridad, informes, dashboards, almacenamiento, integración, migración.
- Marca explícitamente lo pendiente (`[Pendiente de definir con el cliente]`) en cualquier
  sección sin datos suficientes — nunca lo completa a criterio propio.

## Qué necesitás del usuario

Como mínimo: `gap_id`, `gap_nombre`, `cliente` — sin esto no se genera nada (son
obligatorios, `render_fdd()` tira `ValueError` si faltan). Todo lo demás es opcional y se
marca como pendiente si no está.

## Flujo

1. Armá el diccionario de datos siguiendo la estructura documentada en el docstring de
   `scripts/build_fdd_html.py` — 13 claves, una por sección, todas opcionales salvo las 3
   obligatorias de arriba.
2. Llená cada sección con lo que realmente aporten las Historias/notas del usuario — no
   inventes campos de tabla, roles de seguridad, o integraciones que no se mencionaron.
3. Generá el archivo:

```python
import sys
sys.path.insert(0, "scripts")
from build_fdd_html import render_fdd, save

data = { ... }  # ver estructura en el docstring del script
save(render_fdd(data), "outputs/FDD-GAP-{id}-{nombre}.html")
```

4. Compartí el archivo con `present_files` — es el output final, no hace falta convertirlo a
   nada más salvo que el usuario pida explícitamente un PDF (en cuyo caso, indicale que puede
   abrirlo en el navegador e imprimir a PDF desde ahí — esta skill no genera el PDF por sí sola).

## Compatibilidad — evitar CSS que no renderiza en todos lados

Encontramos tres problemas reales al probar el HTML generado contra un motor de renderizado
más viejo (no todos los visores/impresoras usan un browser moderno):

- **`min-height: 100vh` en la portada se comporta mal fuera de un browser real** — se
  reemplazó por una altura fija (`900px`). No lo vuelvas a cambiar a `vh` sin probarlo.
- **`gap` en flexbox no lo soportan motores WebKit viejos** (ej. wkhtmltopdf/wkhtmltoimage,
  herramientas comunes para convertir HTML a PDF) — se reemplazó por `margin` explícito en
  los elementos hijos. Si agregás un layout flex nuevo, usá `margin`, no `gap`.
- **Bebas Neue se carga desde Google Fonts (`@import` en el CSS) — requiere internet.** Sin
  conexión, cae al fallback `sans-serif` del sistema (se ve razonable igual, solo pierde el
  estilo condensado). Segoe UI viene preinstalada en Windows; en Mac/Linux cae también a un
  sans-serif del sistema. Ninguno de los dos casos rompe el documento, solo cambia el look.

## Restricciones

- No generés el documento sin `gap_id`, `gap_nombre`, y `cliente` — son obligatorios.
- No inventes contenido de ninguna sección — todo lo que no venga de las Historias/notas del
  usuario se marca como `[Pendiente de definir con el cliente]`, nunca se completa a criterio
  propio (mismo principio que todas las skills de Fase 1).
- No modifiques `assets/logo-axxon.png` ni `assets/logo-evolucion-digital.png` — el primero
  es el logo actual de Axxon (extraído del template PPTX de `kickoff-brief`, Fase 0 — no del
  Word original del FDD, que tenía una versión vieja del mark), el segundo del template Word.
- No reintroduzcas `100vh` ni `gap` de flexbox sin probar contra un renderizador no-browser
  primero — ver "Compatibilidad" arriba.
