# Tareas: Filtro de sesiones raíz

## Review Workload Forecast

| Campo | Valor |
|-------|-------|
| Líneas cambiadas estimadas | 320-420 |
| Riesgo presupuesto 400 líneas | Medium |
| Chained PRs recomendados | No |
| División sugerida | PR único con commits por unidad |
| Delivery strategy | auto-forecast |
| Chain strategy | pending |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Medium

### Unidades de trabajo sugeridas

| Unidad | Objetivo | PR probable | Notas |
|------|------|-----------|-------|
| 1 | Propagar `parent_id` y reglas de vista en dominio/aplicación | PR 1 | Incluir tests de repo y aplicación. |
| 2 | Integrar toggle/render TUI, docs y verificación final | PR 1 | Mantener selección, ayuda inferior y README. |

## Fase 1: Datos y dominio

- [x] 1.1 Actualizar `tests/test_sqlite_repo.py` con `parent_id` nullable y caso de columna ausente legible.
- [x] 1.2 Modificar `src/opencode_session_navigator/infra/sqlite_repo.py` para leer/validar `session.parent_id` sin cambiar `mode=ro` ni `session.directory = ?`.
- [x] 1.3 Actualizar `src/opencode_session_navigator/domain.py` para conservar `parent_id` y metadata visual derivada sin afectar matching.

## Fase 2: Estado de aplicación

- [x] 2.1 Agregar en `tests/test_application.py` escenarios de raíces por defecto, búsqueda de hija con raíz contextual, huérfanas y selección estable.
- [x] 2.2 Modificar `src/opencode_session_navigator/application.py` con `SessionViewMode`, `with_view_mode()` y orden raíz→hijas/huérfanas.
- [x] 2.3 Verificar que la búsqueda evalúe todas las sesiones del `cwd` exacto aunque la vista activa sea raíces.

## Fase 3: TUI y documentación

- [x] 3.1 Ampliar `tests/test_tui.py` para atajo visible, toggle raíz/todas, prefijos y apertura de raíz contextual real.
- [x] 3.2 Modificar `src/opencode_session_navigator/tui.py` para binding de toggle, estado inferior y render tipo árbol sin headers inertes.
- [x] 3.3 Actualizar `README.md` con modo raíz por defecto, modo “todas” y nuevo atajo.

## Fase 4: Verificación

- [x] 4.1 Ejecutar `uv run pytest`; esperar cobertura verde de repo, aplicación y TUI para los escenarios del delta spec.
- [x] 4.2 Ejecutar `uv run ruff check .`, `uv run ruff format --check .` y `uv run mypy`; corregir hallazgos antes de cerrar.
- [x] 4.3 Revisar manualmente `git diff --stat` durante apply y dividir antes de PR si el cambio real supera claramente 400 líneas; evidencia registrada en `apply-progress.md`.
