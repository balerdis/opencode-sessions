# Propuesta: Navegador de sesiones de OpenCode

## Intento

Crear una TUI Python/Textual para recuperar sesiones de OpenCode del `cwd` exacto y reabrirlas sin los límites de la TUI nativa. Ayuda a volver a un proyecto y encontrar rápido una sesión previa por título, prompt, descripción o resumen.

## Problema y brecha actual

OpenCode filtra por fecha, alcance, `path`, límite y búsqueda solo por título. Eso oculta sesiones útiles en SQLite y obliga a recordar IDs o revisar la base manualmente.

## Alcance

### Incluido
- Ejecutable desde cualquier directorio; resuelve `Path.cwd().resolve()`.
- Descubre la DB con `opencode db path` y la abre en modo solo lectura/defensivo.
- Lista sesiones con `session.directory = cwd` exacto.
- TUI Textual con búsqueda interactiva sobre título + descripción + resumen.
- Filas con título, fecha/id, descripción truncada con `...` y resumen heurístico.
- Selección que ejecuta `opencode --session <id>` y al volver restaura lista, filtro y selección.

### Fuera de alcance
- Coincidencia por padres/subdirectorios, edición de DB, sincronización remota, modo CLI de búsqueda, resumen con LLM y compatibilidad garantizada con esquemas futuros.

## Capacidades

### Nuevas capacidades
- `session-navigator`: navegación TUI por cwd exacto, búsqueda enriquecida y reapertura con restauración de estado.

### Capacidades modificadas
- Ninguna; no hay specs existentes.

## Flujos UX y requisitos PRD

- Vacío: mostrar cwd detectado y mensaje accionable si no hay sesiones.
- Buscar: filtrar en memoria preservando selección cuando sea posible.
- Abrir: suspender/ceder terminal a OpenCode; al salir, restaurar la TUI.
- Datos parciales: tolerar títulos, mensajes o partes faltantes con placeholders claros.

## Enfoque y primer slice

Modelo v1: SQLite read-only + adaptador defensivo + modelo en memoria. Usar `session` para listado y `message` + `part` para descripción/resumen; `session_message` local no contiene transcript conversacional completo. Primer slice: package Python, consulta mínima, derivación textual, TUI, handoff/restore y tests con fixtures SQLite.

## Áreas afectadas

| Área | Impacto | Descripción |
|---|---|---|
| `pyproject.toml` | Nuevo | Paquete, dependencia Textual y entry point. |
| `src/...` | Nuevo | DB, modelo, búsqueda, TUI y launcher. |
| `tests/...` | Nuevo | Fixtures SQLite, truncado, búsqueda y restauración. |

## Riesgos, supuestos y mitigación

| Riesgo | Prob. | Mitigación |
|---|---:|---|
| Esquema SQLite interno cambia | Media | Validación de columnas y fallback legible. |
| Scan por `directory` sin índice | Media | Medir antes de optimizar; mantener query simple. |
| Terminal queda mal al lanzar OpenCode | Media | Diseñar suspensión/restauración explícita en Textual. |

## Rollback

Eliminar entry point, `src/...` y tests nuevos; no hay migraciones ni escrituras sobre la DB.

## Criterios de éxito

- [ ] Desde cualquier cwd lista solo sesiones cuyo `session.directory` coincide exactamente.
- [ ] La búsqueda encuentra coincidencias en título, descripción y resumen.
- [ ] `opencode --session <id>` abre la sesión y al volver conserva filtro/selección.
