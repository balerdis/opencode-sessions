# Tareas: Navegador de sesiones de OpenCode

## Review Workload Forecast

| Campo | Valor |
|-------|-------|
| Líneas cambiadas estimadas | 700-1.000 |
| Riesgo del presupuesto de 400 líneas | High |
| PRs encadenados recomendados | Yes |
| División sugerida | PR 1: base Python + dominio/DB → PR 2: búsqueda/texto → PR 3: TUI y apertura |
| Estrategia de entrega | auto-forecast |
| Estrategia de cadena | stacked-to-main |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

### Unidades de trabajo sugeridas

| Unidad | Objetivo | PR probable | Notas |
|------|------|-----------|-------|
| 1 | Configurar paquete, calidad y lectura SQLite defensiva | PR 1 | Incluye fixtures y tests de cwd exacto/esquema. |
| 2 | Construir modelo de filas, texto y búsqueda en memoria | PR 2 | Depende de PR 1; incluye truncado, resumen y selección. |
| 3 | Integrar Textual, launcher y documentación mínima | PR 3 | Depende de PR 2; verifica restauración sin OpenCode real. |

## Fase 1: Base del proyecto y tooling

- [x] 1.1 Crear `pyproject.toml` con `uv`, paquete `opencode-session-navigator`, dependencia `textual`, entry point, `pytest`, `ruff` y type checker práctico.
- [x] 1.2 Crear layout `src/opencode_session_navigator/` y `tests/`; agregar configuración mínima para `uv run pytest`, `uv run ruff check .` y `uv run ruff format --check .`.
- [x] 1.3 Documentar en `README.md` el uso inicial y aclarar que comentarios/documentación del proyecto van en español.

## Fase 2: Dominio, texto y búsqueda

- [x] 2.1 Crear `src/opencode_session_navigator/domain.py` con `SessionRow`, placeholders claros y texto normalizado buscable.
- [x] 2.2 Crear `src/opencode_session_navigator/text.py` con truncado terminado en `...`, descripción desde usuario y resumen heurístico determinístico.
- [x] 2.3 Crear `src/opencode_session_navigator/application.py` con carga, filtro en memoria y preservación de `selected_id`.
- [x] 2.4 Probar datos parciales, descripción larga, resumen sin assistant, búsqueda fuera del título y preservación de selección.

## Fase 3: Infraestructura SQLite y OpenCode

- [x] 3.1 Crear `infra/opencode_cli.py` para `opencode db path` y `opencode --session <id>` con errores legibles y fakes testeables.
- [x] 3.2 Crear `infra/sqlite_repo.py` con URI `file:{path}?mode=ro`, `uri=True`, validación de tablas/columnas y consultas por `session.directory = cwd` exacto.
- [x] 3.3 Agregar fixtures SQLite para DB válida, cwd vacío, columnas faltantes, JSON/partes desconocidas y garantía de no escritura.
- [x] 3.4 Verificar con `uv run pytest tests/test_sqlite_repo.py` los escenarios de filtrado exacto, esquema incompatible y resiliencia.

## Fase 4: TUI Textual y apertura

- [x] 4.1 Crear `tui.py` con buscador, lista, mensajes de vacío/error, bindings mínimos, render de título/fecha-id/descripción/resumen.
- [x] 4.2 Implementar confirmación que suspende la TUI, ejecuta `opencode --session <id>` y restaura query, lista visible y selección.
- [x] 4.3 Probar la UI con fakes sin lanzar OpenCode real: navegación, apertura y restauración de estado.
- [x] 4.4 Ejecutar verificación final: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .` y, si está configurado, type checker.
