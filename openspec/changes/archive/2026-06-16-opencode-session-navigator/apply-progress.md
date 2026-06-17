# Progreso de aplicación: Navegador de sesiones de OpenCode

## Estado

- Cambio: `opencode-session-navigator`
- Modo: estándar; `strict_tdd` deshabilitado.
- Estrategia de cadena: `stacked-to-main`.
- Slice actual: PR 3 / unidad 3 — TUI Textual, launcher interactivo y restauración de estado.

## Tareas completadas

- [x] 1.1 Crear `pyproject.toml` con `uv`, paquete `opencode-session-navigator`, dependencia `textual`, entry point, `pytest`, `ruff` y type checker práctico.
- [x] 1.2 Crear layout `src/opencode_session_navigator/` y `tests/`; agregar configuración mínima para `uv run pytest`, `uv run ruff check .` y `uv run ruff format --check .`.
- [x] 1.3 Documentar en `README.md` el uso inicial y aclarar que comentarios/documentación del proyecto van en español.
- [x] 2.1 Crear `src/opencode_session_navigator/domain.py` con `SessionRow`, placeholders claros y texto normalizado buscable.
- [x] 2.2 Crear `src/opencode_session_navigator/text.py` con truncado terminado en `...`, descripción desde usuario y resumen heurístico determinístico.
- [x] 2.3 Crear `src/opencode_session_navigator/application.py` con carga, filtro en memoria y preservación de `selected_id`.
- [x] 2.4 Probar datos parciales, descripción larga, resumen sin assistant, búsqueda fuera del título y preservación de selección.
- [x] 3.1 Crear `infra/opencode_cli.py` para `opencode db path` y `opencode --session <id>` con errores legibles y fakes testeables.
- [x] 3.2 Crear `infra/sqlite_repo.py` con URI `file:{path}?mode=ro`, `uri=True`, validación de tablas/columnas y consultas por `session.directory = cwd` exacto.
- [x] 3.3 Agregar fixtures SQLite para DB válida, cwd vacío, columnas faltantes, JSON/partes desconocidas y garantía de no escritura.
- [x] 3.4 Verificar con `uv run pytest tests/test_sqlite_repo.py` los escenarios de filtrado exacto, esquema incompatible y resiliencia.
- [x] 4.1 Crear `tui.py` con buscador, lista, mensajes de vacío/error, bindings mínimos, render de título/fecha-id/descripción/resumen.
- [x] 4.2 Implementar confirmación que suspende la TUI, ejecuta `opencode --session <id>` y restaura query, lista visible y selección.
- [x] 4.3 Probar la UI con fakes sin lanzar OpenCode real: navegación, apertura y restauración de estado.
- [x] 4.4 Ejecutar verificación final: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .` y, si está configurado, type checker.

## Archivos creados o modificados

| Archivo | Acción | Descripción |
|---|---|---|
| `.gitignore` | Creado | Ignora entornos virtuales, caches y bytecode generados por la toolchain Python. |
| `README.md` | Creado | Documenta estado inicial, comandos de verificación, uso temporal y contrato de idioma. |
| `pyproject.toml` | Creado | Configura paquete, entry point, dependencias y herramientas `pytest`, `ruff` y `mypy`. |
| `uv.lock` | Creado | Fija versiones resueltas por `uv` para reproducibilidad del proyecto ejecutable. |
| `src/opencode_session_navigator/__init__.py` | Creado | Declara paquete y versión inicial. |
| `src/opencode_session_navigator/cli.py` | Creado | Entry point ejecutable que resuelve el cwd e inicia la TUI real del navegador. |
| `src/opencode_session_navigator/infra/__init__.py` | Creado | Namespace para adaptadores de infraestructura. |
| `src/opencode_session_navigator/infra/opencode_cli.py` | Creado | Descubre la ruta de DB con fakes testeables y valida comando de sesión. |
| `src/opencode_session_navigator/infra/sqlite_repo.py` | Creado | Abre SQLite en solo lectura, valida esquema y lista sesiones por cwd exacto. |
| `tests/test_opencode_cli.py` | Creado | Cubre descubrimiento de DB, errores legibles y validación de sesión. |
| `tests/test_sqlite_repo.py` | Creado | Cubre cwd exacto, vacío, esquema incompatible, resiliencia JSON y solo lectura. |
| `openspec/changes/opencode-session-navigator/tasks.md` | Modificado | Registra `stacked-to-main` y marca únicamente las tareas completadas. |
| `src/opencode_session_navigator/domain.py` | Creado | Define `SessionRow`, `SessionText`, placeholders de título y texto buscable normalizado. |
| `src/opencode_session_navigator/text.py` | Creado | Agrega normalización, truncado con `...`, descripción desde usuario y resumen heurístico sin servicios externos. |
| `src/opencode_session_navigator/application.py` | Creado | Carga registros, construye filas, filtra en memoria y preserva `selected_id` cuando sigue visible. |
| `tests/test_text.py` | Creado | Cubre normalización, truncado, placeholders, descripción y resumen heurístico. |
| `tests/test_application.py` | Creado | Cubre construcción de filas, búsqueda fuera del título y preservación/reasignación de selección. |
| `src/opencode_session_navigator/tui.py` | Creado | Integra Textual con buscador, tabla, mensajes de vacío/error, controlador testeable, navegación y suspensión para abrir OpenCode. |
| `src/opencode_session_navigator/cli.py` | Modificado | Reemplaza el entry point temporal por la TUI real con cwd resuelto, loader por DB y launcher interactivo. |
| `src/opencode_session_navigator/infra/opencode_cli.py` | Modificado | Agrega `OpenCodeSessionLauncher` con ejecución interactiva por argv seguro para `opencode --session <id>`. |
| `tests/test_tui.py` | Creado | Cubre mensajes de vacío, navegación, filtrado en memoria y restauración de filtro/selección sin lanzar OpenCode real. |
| `tests/test_opencode_cli.py` | Modificado | Agrega cobertura del launcher interactivo y del argv usado para abrir sesiones. |
| `README.md` | Modificado | Documenta el uso actual de la TUI, búsqueda, navegación, apertura y restauración al volver desde OpenCode. |
| `tests/test_tui.py` | Modificado | Agrega pruebas Textual app-level con `run_test()`/pilot para búsqueda, flechas y Enter, más cobertura de errores de carga y launcher. |
| `src/opencode_session_navigator/tui.py` | Modificado | Hace globales las flechas y Enter con bindings prioritarios, y permite probar apertura cuando Textual headless no soporta suspensión. |
| `openspec/config.yaml` | Modificado | Sanitiza metadatos locales versionables sin cambiar la configuración SDD. |
| `openspec/changes/opencode-session-navigator/exploration.md` | Modificado | Sanitiza ruta local de DB y conteos locales, preservando hallazgos técnicos sobre SQLite/OpenCode. |
| `src/opencode_session_navigator/tui.py` | Modificado | Conserva visible el error de recarga si OpenCode sale y falla la recarga posterior. |
| `tests/test_tui.py` | Modificado | Agrega cobertura determinística para salida de OpenCode seguida de fallo de recarga. |
| `openspec/changes/opencode-session-navigator/apply-progress.md` | Modificado | Corrige la descripción obsoleta del entry point `cli.py` y registra esta remediación. |

## Verificación

- `uv run pytest tests/test_sqlite_repo.py` — 9 passed tras remediación.
- `uv run pytest` — 13 passed.
- `uv run ruff check .` — passed.
- `uv run ruff format --check .` — passed.
- `uv run mypy` — passed.
- `uv run pytest` — 25 passed después del PR 2.
- `uv run ruff check .` — passed después del PR 2.
- `uv run ruff format --check .` — passed después del PR 2.
- `uv run mypy` — passed después del PR 2.
- `uv run pytest` — 30 passed tras remediación post-review PR 2.
- `uv run ruff check .` — passed tras remediación post-review PR 2.
- `uv run ruff format --check .` — passed tras remediación post-review PR 2.
- `uv run mypy` — passed tras remediación post-review PR 2.
- `uv run pytest` — 35 passed después del PR 3.
- `uv run ruff check .` — passed después del PR 3.
- `uv run ruff format --check .` — passed después del PR 3.
- `uv run mypy` — passed después del PR 3.
- `uv run pytest` — 40 passed tras remediación post-review PR 3.
- `uv run ruff check .` — passed tras remediación post-review PR 3.
- `uv run ruff format --check .` — passed tras remediación post-review PR 3.
- `uv run mypy` — passed tras remediación post-review PR 3.
- `uv run pytest` — 41 passed tras remediación de confiabilidad PR 3.
- `uv run ruff check .` — passed tras remediación de confiabilidad PR 3.
- `uv run ruff format --check .` — passed tras remediación de confiabilidad PR 3.
- `uv run mypy` — passed tras remediación de confiabilidad PR 3.
- `uv run pytest` — 41 passed tras remediación final de wording PR 3.
- `uv run ruff check .` — passed tras remediación final de wording PR 3.
- `uv run ruff format --check .` — passed tras remediación final de wording PR 3.
- `uv run mypy` — passed tras remediación final de wording PR 3.

## Remediación post-review PR 1

- `infra/opencode_cli.py`: `default_runner()` convierte `FileNotFoundError` en `OpenCodeCliError` con mensaje accionable cuando no existe el comando `opencode`.
- `infra/sqlite_repo.py`: las fallas `sqlite3.DatabaseError` durante validación de esquema y consultas se envuelven en `SQLiteRepositoryError` con mensaje legible, sin ocultar `IncompatibleSchemaError`.
- `tests/test_opencode_cli.py`: agrega cobertura behavior-first para CLI faltante.
- `tests/test_sqlite_repo.py`: agrega cobertura para DB corrupta, fallo de apertura, fallo durante validación y prueba que el adaptador invoca SQLite con URI `mode=ro` y `uri=True`.
- `.gitignore`: ignora metadatos operativos locales `.codegraph/` y `.atl/`; los artefactos OpenSpec se mantienen versionables.

## Remediación post-review PR 2

- `text.py`: el truncado ahora respeta siempre `max_length`; para límites 1 y 2 devuelve `.` y `..`, y conserva `...` para límites de 3 o mayores.
- `text.py`, `domain.py`, `application.py` y `sqlite_repo.py`: la normalización común elimina secuencias ANSI/OSC y caracteres de control antes de preparar texto visible o buscable, manteniendo la compactación normal de espacios.
- `infra/sqlite_repo.py`: `message.time_created` queda declarado como columna requerida porque `_load_texts()` ordena por ese campo; si falta, se reporta `IncompatibleSchemaError`.
- `tests/test_text.py`, `tests/test_application.py` y `tests/test_sqlite_repo.py`: agregan cobertura para límites 1/2, truncado de descripciones cargadas desde registros, sanitización de títulos/mensajes/descripciones y esquema incompatible sin `message.time_created`.

## Remediación post-review PR 3

- `tests/test_tui.py`: agrega prueba app-level de Textual con `run_test()`/pilot para validar escritura en el buscador, navegación con flecha y apertura con Enter sobre `SessionNavigatorApp`, no solo sobre el controlador.
- `tests/test_tui.py`: agrega cobertura determinística de fallo de carga, `OpenCodeCliError`, `OSError` y código no cero del launcher, verificando mensajes visibles y restauración de estado.
- `src/opencode_session_navigator/tui.py`: las flechas y Enter usan bindings prioritarios para funcionar aunque el buscador tenga foco; `j`/`k` quedan disponibles cuando el foco no captura texto.
- `src/opencode_session_navigator/tui.py`: si el entorno de prueba/headless no soporta `App.suspend()`, la apertura se ejecuta sin suspensión para mantener el comportamiento testeable; en terminal normal se sigue usando suspensión.
- `README.md`: aclara el comportamiento confiable de navegación con `↑`/`↓` mientras el buscador tiene foco y el alcance real de `j`/`k`.
- `openspec/config.yaml` y `exploration.md`: se sanitizaron ruta local de DB, path local de `uv` y conteos de sesiones locales sin eliminar artefactos requeridos.

## Remediación de confiabilidad PR 3

- `src/opencode_session_navigator/tui.py`: después de volver de `opencode --session <id>`, `open_selected()` ya no pisa el mensaje visible cuando la recarga falla; conserva `error_message` y el estado accionable definido por `load()`.
- `tests/test_tui.py`: agrega una prueba determinística donde OpenCode termina correctamente, la recarga posterior falla y la TUI mantiene visible el error real en vez de mostrar éxito.
- `openspec/changes/opencode-session-navigator/apply-progress.md`: actualiza la descripción de `cli.py` para reflejar que ahora es el entry point real de la TUI, no un paso temporal.

## Desviaciones o notas

- El repositorio mantiene `SessionRecord` de infraestructura como primitiva mínima; `application.py` lo convierte a `SessionRow` de dominio sin acoplar la TUI futura a SQLite.
- La TUI usa `DataTable` de Textual y un `TuiSessionController` testeable; además, la remediación PR 3 cubre el flujo app-level crítico con el pilot de Textual para búsqueda, flechas y Enter.
- Se incluye `uv.lock` en el slice porque este repositorio funciona como aplicación/herramienta ejecutable y conviene preservar instalaciones reproducibles desde el primer PR.
- La búsqueda normaliza espacios y mayúsculas/minúsculas con `casefold`, pero no aplica stemming, ranking ni eliminación de acentos; eso mantiene el filtro v1 simple, determinístico y barato.
- Al volver desde OpenCode, el controlador recarga los datos mediante el loader y reaplica `query` + `selected_id`; si OpenCode termina con código distinto de cero, la TUI conserva un mensaje legible sin afirmar que la lista anterior exacta siguió vigente.
- Si OpenCode sale pero falla la recarga posterior, la TUI prioriza el error de recarga sobre mensajes de éxito o restauración para no ocultar el fallo operativo.

## Remediación final de wording PR 3

- `src/opencode_session_navigator/tui.py`: el mensaje de salida no cero de OpenCode ahora indica que la TUI se recargó con filtro y selección restaurados, sin prometer que la lista anterior exacta se mantuvo cuando el loader pudo haber cambiado los datos.
- `tests/test_tui.py`: actualiza la cobertura del retorno no cero para exigir el wording preciso y bloquear la frase inexacta `lista anterior`.

## Próximo trabajo recomendado

- Continuar con la fase de verificación SDD para revisar el cambio completo contra propuesta, especificación, diseño y tareas.
