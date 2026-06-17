# Diseño: Navegador de sesiones de OpenCode

## Enfoque técnico

Implementar una TUI Python con Textual que resuelve `Path.cwd().resolve()`, descubre la base con `opencode db path`, lee SQLite en modo solo lectura y construye un modelo en memoria para búsqueda interactiva. El primer slice privilegia una consulta simple y derivación textual determinística sobre `session`, `message` y `part`; no edita la DB ni promete compatibilidad estable con esquemas futuros.

## Decisiones de arquitectura

| Decisión | Elección | Alternativas consideradas | Fundamento |
|---|---|---|---|
| Capas | Dominio + aplicación + infraestructura + UI Textual | Script único | Mantiene testeables DB, heurísticas y estado sin acoplarlos a widgets. |
| Fuente de datos | SQLite read-only vía `opencode db path` | API/CLI de listado o `opencode export` | Evita límites upstream de fecha, `path`, búsqueda por título y `limit`; `export` sería lento para búsqueda. |
| Filtro v1 | `session.directory = cwd_resuelto` exacto | Padres/subdirectorios/`path` relativo | Coincide con la spec y reduce ambigüedad. |
| Extracción textual | `message` + `part` JSON, ignorando tipos desconocidos | `session_message` como fuente primaria | En la DB local `session_message` no contiene transcript conversacional útil. |
| Resumen | Heurística barata: último texto assistant legible; fallback a compaction/descripción/placeholder | LLM o resumen avanzado | Determinístico, sin red y suficiente para v1. |

## Estructura propuesta

| Archivo | Acción | Descripción |
|---|---|---|
| `pyproject.toml` | Crear | Paquete, dependencia `textual`, entry point. |
| `src/opencode_session_navigator/domain.py` | Crear | `SessionRow`, `SessionText`, placeholders y normalización. |
| `src/opencode_session_navigator/application.py` | Crear | Carga, filtrado en memoria, preservación de selección y estado. |
| `src/opencode_session_navigator/infra/opencode_cli.py` | Crear | `opencode db path` y `opencode --session <id>`. |
| `src/opencode_session_navigator/infra/sqlite_repo.py` | Crear | Apertura read-only, validación de esquema y queries. |
| `src/opencode_session_navigator/text.py` | Crear | Truncado, descripción y resumen heurístico. |
| `src/opencode_session_navigator/tui.py` | Crear | App Textual, bindings, render de lista y errores. |
| `tests/...` | Crear | Fixtures SQLite y tests de capa. |

## Flujo de datos

```text
cwd ─→ db path ─→ SQLite read-only ─→ filas dominio ─→ filtro en memoria ─→ Textual
                                      │                              │
                                      └── heurísticas texto          └── opencode --session
```

## Contratos internos

- Dominio: `SessionRow(id, title, context, description, summary, searchable_text, updated_at)`.
- Repositorio: `list_sessions(cwd: Path) -> list[SessionRow]`; valida tablas/columnas requeridas antes de consultar.
- Estado UI: `all_sessions`, `visible_sessions`, `query`, `selected_id`, `status/error`. Al filtrar, conservar `selected_id` si sigue visible; si no, seleccionar el primer resultado.
- DB: abrir con URI `file:{path}?mode=ro` y `uri=True`; nunca ejecutar escrituras ni migraciones.

## Consulta y extracción

La query base lee sesiones por `directory` exacto, ordenadas por `time_updated` descendente, sin límite artificial. Para cada sesión, obtener textos candidatos de `message`/`part` con `json_extract(... '$.role')` y partes `type = text`; descripción = primer texto de usuario útil. Resumen = último texto assistant útil acortado; fallback a compaction si aparece, luego descripción, luego placeholder. Si falta una tabla/columna requerida, mostrar incompatibilidad de esquema sin traceback crudo.

## Navegación y handoff

Bindings mínimos: escribir en buscador, flechas/j-k para moverse, Enter para abrir, Esc/q para salir. Al confirmar, guardar `query` y `selected_id`, suspender la app con la API de Textual para procesos externos, ejecutar `opencode --session <id>` de forma interactiva y restaurar la pantalla al terminar. Tras volver, refrescar datos opcionalmente sin perder filtro ni selección.

## Manejo de errores

Errores de CLI, DB ausente, permisos, esquema incompatible o JSON inválido se convierten en mensajes accionables dentro de la TUI. JSON/partes desconocidas se ignoran si hay texto válido restante.

## Estrategia de pruebas

| Capa | Qué probar | Enfoque |
|---|---|---|
| Unidad | normalización, truncado con `...`, heurística, preservación de selección | `pytest` cuando se configure. |
| Integración | SQLite fixture read-only, columnas faltantes, cwd exacto | DB temporal con esquema mínimo. |
| UI/proceso | bindings, estado antes/después de launcher | Tests con fakes; evitar lanzar OpenCode real. |

## Migración y extensión

No requiere migración. Extensiones futuras: filtro por árbol, soporte `session_message`, paginación/índices si la DB crece, summaries avanzados y modo de exportación.

## Preguntas abiertas

- Ninguna bloqueante para v1.
