# Diseño: Filtro de sesiones raíz

## Enfoque técnico

Propagar `session.parent_id` desde SQLite hasta `SessionRow`, cargar siempre el conjunto del `cwd` exacto y derivar la vista visible en aplicación. La TUI solo alterna el modo y renderiza prefijos; no conoce SQL ni reconstruye jerarquía. La DB de OpenCode sigue en solo lectura y el filtro `session.directory = Path.cwd().resolve()` no cambia.

## Decisiones de arquitectura

| Tema | Opción / tradeoff | Decisión y razón |
|---|---|---|
| Filtro raíz | Filtrar en SQL ahorra filas, pero rompe búsqueda global de hijas. | Cargar todas las sesiones del `cwd` y filtrar en memoria; permite raíz por defecto, búsqueda contextual y modo “todas” sin reconsultas. |
| Modelo visible | Usar headers inertes simplifica el árbol, pero no se pueden abrir. | Toda fila visible será una `SessionRow` real; agregar metadata derivada (`parent_id`, `kind`, `depth`, `title_prefix`/`display_title`). |
| Orden | Recencia plana mezcla hijos; DFS puro puede ocultar actividad reciente de raíces. | Ordenar grupos por recencia de la raíz y ordenar hijos por recencia dentro del grupo; huérfanos al final por recencia. |
| Esquema | Tratar `parent_id` como opcional degrada silenciosamente. | Validarlo como columna requerida y fallar con `IncompatibleSchemaError`; el spec exige incompatibilidad legible si falta. |

## Flujo de datos

```text
SQLiteSessionRepository ──parent_id──> SessionRecord
        │                               │
        └─ cwd exacto, read-only         ▼
SessionNavigator.record_to_row ──> SessionRow(parent_id)
                                      │
SessionListState(view_mode, query) ───┴─> visible_sessions ordenadas
                                      │
SessionNavigatorApp ──prefijos/tree──> DataTable ──Enter──> opencode --session <id>
```

## Cambios por archivo

| Archivo | Acción | Descripción |
|---|---|---|
| `src/opencode_session_navigator/infra/sqlite_repo.py` | Modificar | Agregar `parent_id` a `SessionRecord`, `required_columns` y `SELECT`; mantener `WHERE directory = ?` y orden base por recencia. |
| `src/opencode_session_navigator/domain.py` | Modificar | Agregar `parent_id: str | None` y campos visuales derivados para árbol/contexto sin afectar matching. |
| `src/opencode_session_navigator/application.py` | Modificar | Introducir `SessionViewMode` (`roots`, `all`), `with_view_mode()`, agrupación raíz→hijos, búsqueda global en modo raíz y preservación de selección. |
| `src/opencode_session_navigator/tui.py` | Modificar | Agregar binding de toggle, pasar modo en recarga/restauración, actualizar estado inferior y renderizar título con prefijo. |
| `tests/*` | Modificar | Cubrir repositorio, aplicación y TUI con jerarquía, búsqueda contextual, huérfanos, toggle y selección. |
| `README.md`, `openspec/specs/session-navigator/spec.md` | Modificar luego | Documentar contrato visible al archivar/aplicar el cambio. |

## Contratos

- `SessionRecord.parent_id: str | None` conserva el valor crudo de SQLite.
- `SessionRow.parent_id: str | None` define raíz con `None`.
- `SessionListState.view_mode` inicia en `roots`.
- En modo `roots` sin query: visibles = raíces.
- En modo `roots` con query: evaluar todas las filas; mostrar raíces coincidentes y, para hijas coincidentes, su raíz disponible inmediatamente antes. La raíz contextual es seleccionable/abrible.
- En modo `all`: mostrar cada raíz seguida por sus hijas; las hijas cuyo padre no está en el conjunto del `cwd` aparecen como huérfanas identificadas.
- `with_selected_id()` y cambios de query/modo preservan `selected_id` si sigue visible; si no, seleccionan la primera fila visible.

## Estrategia de pruebas

| Capa | Qué probar | Enfoque |
|---|---|---|
| Infra | `parent_id` leído, requerido y sin cambiar `cwd`. | SQLite temporal; actualizar helpers para columna nullable. |
| Dominio/App | raíces por defecto, búsqueda de hijas con contexto, all agrupado, huérfanos y selección. | Tests unitarios con `SessionRecord`/`SessionRow` falsos. |
| TUI | binding visible, toggle, render prefijado y apertura de raíz contextual. | `TuiSessionController` y `app.run_test()` con fakes. |

## Migración / compatibilidad

No hay migración: la DB de OpenCode no se escribe. Bases sin `session.parent_id` se tratarán como esquema incompatible con mensaje legible. Esto es deliberado porque el nuevo comportamiento depende de esa columna.

## Riesgos y mitigaciones

- **Profundidad mayor a una**: primera entrega agrupa por `parent_id` directo; nietos quedan como hijos de su padre si el padre existe o como huérfanos si no está visible.
- **Recencia menos obvia**: estado inferior debe indicar modo activo; tests fijan orden raíz→hijos.
- **Confundir contexto con header**: no se crean headers inertes; toda fila mantiene `id` real.

## Preguntas abiertas

Ninguna bloqueante.
