# Apply Progress: root-session-filter

## Mode

Standard apply mode. Strict TDD was not active (`openspec/config.yaml` has `strict_tdd: false`).

## Completed Tasks

- [x] 1.1 Actualizar `tests/test_sqlite_repo.py` con `parent_id` nullable y caso de columna ausente legible.
- [x] 1.2 Modificar `src/opencode_session_navigator/infra/sqlite_repo.py` para leer/validar `session.parent_id` sin cambiar `mode=ro` ni `session.directory = ?`.
- [x] 1.3 Actualizar `src/opencode_session_navigator/domain.py` para conservar `parent_id` y metadata visual derivada sin afectar matching.
- [x] 2.1 Agregar en `tests/test_application.py` escenarios de raíces por defecto, búsqueda de hija con raíz contextual, huérfanas y selección estable.
- [x] 2.2 Modificar `src/opencode_session_navigator/application.py` con `SessionViewMode`, `with_view_mode()` y orden raíz→hijas/huérfanas.
- [x] 2.3 Verificar que la búsqueda evalúe todas las sesiones del `cwd` exacto aunque la vista activa sea raíces.
- [x] 3.1 Ampliar `tests/test_tui.py` para atajo visible, toggle raíz/todas, prefijos y apertura de raíz contextual real.
- [x] 3.2 Modificar `src/opencode_session_navigator/tui.py` para binding de toggle, estado inferior y render tipo árbol sin headers inertes.
- [x] 3.3 Actualizar `README.md` con modo raíz por defecto, modo “todas” y nuevo atajo.
- [x] 4.1 Ejecutar `uv run pytest`; esperar cobertura verde de repo, aplicación y TUI para los escenarios del delta spec.
- [x] 4.2 Ejecutar `uv run ruff check .`, `uv run ruff format --check .` y `uv run mypy`; corregir hallazgos antes de cerrar.
- [x] 4.3 Revisar manualmente `git diff --stat` durante apply y dividir antes de PR si el cambio real supera claramente 400 líneas; evidencia registrada abajo.

## Implementation Summary

- `SessionRecord` and `SessionRow` now preserve `parent_id`.
- SQLite schema validation requires `session.parent_id` and keeps read-only access plus exact `cwd` filtering unchanged.
- Application state now supports root and all-sessions modes, contextual root search results, tree-like grouping, orphans, and stable selection.
- TUI exposes `Ctrl+T`, renders derived display titles, restores the current view mode after OpenCode handoff, and keeps contextual root rows openable.
- README and AGENTS documentation now describe the root/default and all-sessions modes.

## Verification

| Command | Result |
|---------|--------|
| `uv run pytest` | Passed: 54 tests |
| `uv run ruff check .` | Passed |
| `uv run ruff format --check .` | Passed |
| `uv run mypy` | Passed |

## Review Budget

Manual evidence from apply: `git diff --stat` was reviewed during implementation. The tracked implementation diff before artifact updates was `9 files changed, 396 insertions(+), 35 deletions(-)`, within the configured review budget line forecast and not clearly above the 400-line risk threshold. This checkbox is manual review evidence, not an automated proof.

Remediation note: warning-focused test/artifact additions after review increase the working-tree diff beyond the original implementation stat. No automated size-budget proof is claimed here, and no PR was created in this remediation pass.

## Warning Remediation

- Added app-level Textual tests for visible `Ctrl+T` help/footer presence and DataTable tree-prefix rendering.
- Added hierarchy edge tests for a root with two children, deterministic child placement when a newer child appears before its parent in base order, and a SQLite-backed cross-cwd parent boundary that leaves the child as an orphan.

## Deviations

None — implementation follows the approved design. The canonical OpenSpec spec was left unchanged for the archive phase to sync the accepted delta.
