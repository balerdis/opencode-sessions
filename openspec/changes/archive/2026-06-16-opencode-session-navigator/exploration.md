## Exploration: opencode-session-navigator

### Estado actual

El repositorio `opencode-sessions` está inicializado para SDD, pero todavía no tiene código de producto Python. La configuración actual (`openspec/config.yaml`) declara que el stack será Python, que aún no hay runner de tests ni convenciones propias, y que el acceso a la base de OpenCode debe ser de solo lectura salvo que una especificación posterior indique lo contrario.

La investigación upstream se hizo sobre OpenCode `v1.17.7`, tag `4ed4f749e644ffb5b279fb30b7b915e743d80142` en `anomalyco/opencode` (repositorio actual visto también como `opencode-ai/opencode`). No encontré documentación pública de usuario que describa el esquema SQLite local como contrato estable. Sí existen especificaciones internas y código fuente relevantes: `specs/v2/session.md`, `specs/storage/remove-opencode-db.md`, `packages/core/src/session/sql.ts`, `packages/core/src/session.ts`, `packages/opencode/src/session/session.ts`, `packages/tui/src/context/sync.tsx` y `packages/tui/src/component/dialog-session-list.tsx`.

Evidencia upstream principal:

- `packages/core/src/database/database.ts` define la ruta de DB: `Global.Path.data/opencode.db` para canales `latest`, `beta` y `prod`, con override por `OPENCODE_DB`; el CLI `packages/opencode/src/cli/cmd/db.ts` imprime esa ruta con `opencode db path`.
- `packages/core/src/session/sql.ts` define la tabla `session` con `id`, `project_id`, `workspace_id`, `parent_id`, `slug`, `directory`, `path`, `title`, `version`, `metadata`, métricas de resumen/diff, uso, permisos y timestamps. También define `message`, `part`, `session_message`, `session_input` y `session_context_epoch`.
- `packages/core/src/session.ts` lista sesiones V2 filtrando por `SessionTable.directory` cuando el input incluye `directory`; busca solo por `SessionTable.title`; ordena por `time_created`; y aplica `limit` si se envía.
- `packages/opencode/src/session/session.ts` conserva la API/consulta V1 usada por el TUI actual: `listByProject(...)` filtra por `project_id`, opcionalmente por `path`, `directory`, `roots`, `start`, `search` sobre `title`, y usa `limit` por defecto 100. `listGlobal(...)` también limita por defecto a 100 y excluye archivadas salvo `archived`.
- `packages/tui/src/context/sync.tsx` carga sesiones del TUI con `start: Date.now() - 30 días` y con filtro por `path` relativo al worktree cuando está habilitado. Esto explica por qué la UI puede ocultar sesiones aunque existan en SQLite.
- `packages/tui/src/component/dialog-session-list.tsx` muestra solo sesiones raíz (`parentID === undefined`), reordena por `time.updated`, y al buscar llama al API con `search`, `limit: 30` y el mismo filtro de sesión.
- `packages/core/src/session/message.ts` muestra que la proyección V2 `session_message` tiene tipos `user`, `assistant`, `compaction`, etc.; sin embargo la DB local actual solo tiene `agent-switched` y `model-switched` en esa tabla, por lo que para v1 conviene usar `message` + `part` como fuente principal de descripción/resumen.

Validación local contra SQLite:

- `opencode --version`: `1.17.7`.
- `opencode db path`: devuelve la ruta local versionable únicamente como comportamiento del CLI; el artefacto no fija una ruta de usuario.
- La tabla local `session` coincide con los campos upstream relevantes: `id`, `project_id`, `parent_id`, `slug`, `directory`, `title`, `version`, `time_created`, `time_updated`, `workspace_id`, `path`, `agent`, `model`, `cost`, tokens y `metadata`.
- La DB local validada contiene sesiones para distintos directorios y confirma que el filtro por `session.directory = cwd` exacto puede devolver un subconjunto menor que el listado global.
- La tabla local `session_message` existe, pero solo contiene `model-switched` y `agent-switched`; no hay mensajes conversacionales para la sesión raíz actual. En cambio `message` y `part` contienen prompts y respuestas V1, por ejemplo partes `text`, `tool`, `reasoning`, `step-start`, `step-finish`.

Campos y joins candidatos para v1:

- Filtro exacto de cwd: `session.directory = :cwd`, con `cwd` resuelto desde `Path.cwd().resolve()` antes de abrir la DB. No usar `path` ni inferir subdirectorios en v1.
- Sesiones visibles: decidir explícitamente si se muestran solo raíz (`session.parent_id IS NULL`) o todas. Dado el pedido de sesiones asociadas al cwd y el ejemplo de UI raíz, la primera propuesta debería usar raíz por defecto y dejar hijos como detalle futuro, o justificar mostrar todas.
- Título: `session.title`.
- Fecha/contexto: `session.time_updated` para recencia visible; `session.time_created` como fecha de creación; `session.id` abreviable para contexto.
- Descripción: primera parte textual de usuario por sesión, desde `message` + `part`: `message.session_id = session.id`, `json_extract(message.data, '$.role') = 'user'`, `part.message_id = message.id`, `json_extract(part.data, '$.type') = 'text'`, `json_extract(part.data, '$.text')`. Truncar siempre con `...` cuando exceda el ancho/límite.
- Resumen heurístico: primero intentar última parte textual de assistant legible; si existe una parte `compaction`, puede usarse como resumen breve; si no, derivar de las primeras frases de texto assistant o de la descripción. Mantenerlo determinístico y barato, sin LLM.
- Búsqueda TUI: filtrar en memoria sobre `title + description + summary` normalizado, porque OpenCode upstream busca solo `title`.
- Apertura: usar `opencode --session <session_id>` como proceso hijo interactivo; al salir, reanudar la TUI sin reconstruir estado de filtro/selección, aunque se puede refrescar la lista de fondo después.

### Áreas afectadas

- `openspec/changes/opencode-session-navigator/exploration.md` — artefacto de exploración de esta fase.
- `pyproject.toml` — futuro paquete Python, dependencias (`textual`) y entry point ejecutable desde cualquier directorio.
- `src/...` — futura implementación: descubrimiento de DB, repositorio SQLite read-only, derivación de descripción/resumen, estado de búsqueda/selección y lanzamiento de OpenCode.
- `tests/...` — futuros tests unitarios para consultas SQLite, truncado, búsqueda y restauración de estado.

### Enfoques

1. **SQLite read-only con Textual y modelo derivado en memoria** — Consultar directamente la DB local de OpenCode en modo solo lectura, construir filas enriquecidas y filtrar en memoria.
   - Pros: cumple el objetivo sin los límites de la TUI upstream; preserva exact-cwd; búsqueda amplia sobre campos derivados; fácil de testear con fixtures SQLite.
   - Cons: depende de un esquema SQLite interno no documentado como contrato público; hay que tolerar variaciones entre V1/V2 (`message`/`part` vs `session_message`).
   - Esfuerzo: Medio.

2. **Usar API/CLI de OpenCode para listar y solo SQLite para enriquecer** — Invocar APIs o comandos existentes para listar y consultar SQLite para completar campos faltantes.
   - Pros: se apoya más en comportamiento soportado por OpenCode; menor riesgo si cambia parte del storage.
   - Cons: hereda límites upstream (`start` 30 días, `limit` 30/50/100, búsqueda solo por título, scope/path); no satisface bien el objetivo de navegador irrestricto.
   - Esfuerzo: Medio.

3. **Exportar sesiones al seleccionar y generar vista desde JSON** — Listar IDs desde SQLite y usar `opencode export` para obtener detalle cuando haga falta.
   - Pros: evita parsear tanto JSON interno de `part.data` para detalles profundos.
   - Cons: demasiado lento para navegación; complica búsqueda interactiva; no conviene para primera pantalla.
   - Esfuerzo: Alto.

### Recomendación

Usar el enfoque 1 para v1: SQLite read-only + Textual + modelo en memoria. La propuesta debe declarar explícitamente que el esquema de OpenCode es interno y que se implementarán adaptadores defensivos para `message`/`part` y, más adelante, `session_message` si OpenCode migra más tráfico conversacional a V2. Para el primer slice, consultar `session` filtrando por cwd exacto, enriquecer con pocos joins a `message`/`part`, filtrar en memoria y abrir sesiones con `opencode --session <id>` preservando el estado de la pantalla al volver.

### Riesgos

- El esquema SQLite de OpenCode no está documentado como contrato público; puede cambiar entre versiones.
- `session_message` no contiene todavía transcript conversacional completo en la DB local, aunque upstream V2 lo modela; depender solo de esa tabla rompería la descripción/resumen.
- No hay índice local sobre `session.directory`; con bases grandes puede hacer scans. Para v1 probablemente alcanza, pero hay que medir antes de optimizar.
- Abrir `opencode --session` desde dentro de una TUI requiere suspender/ceder correctamente la terminal; si no, puede dejar el terminal en mal estado.
- Si OpenCode actualiza la sesión seleccionada, la lista restaurada puede quedar stale; conviene refrescar al volver sin perder filtro/selección.

### Listo para propuesta

Sí. La propuesta debe mantener el alcance en v1: proyecto Python con Textual, DB read-only descubierta por `opencode db path`, filtro exacto por cwd, filas con título/fecha/id/descripción/resumen heurístico, búsqueda interactiva en memoria, apertura con `opencode --session`, y restauración de estado al volver. No debe prometer compatibilidad estable con futuros esquemas de OpenCode sin una capa de detección/validación.
