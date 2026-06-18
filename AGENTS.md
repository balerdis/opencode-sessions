# Guía para agentes — opencode-sessions

Este repositorio mantiene una TUI en Python/Textual para navegar sesiones locales de OpenCode del directorio actual. Esta guía resume lo que un agente necesita para trabajar de forma segura sin duplicar todo el `README.md`.

## Propósito y alcance actual

- Producto: `opencode-session-navigator`, una TUI para listar, buscar y reabrir sesiones locales de OpenCode asociadas al `cwd` exacto.
- Flujo principal: descubrir la base con `opencode db path`, leer SQLite en modo solo lectura, filtrar por `session.directory`, mostrar raíces por defecto, buscar por título/descripción/resumen y abrir con `opencode --session <id>`.
- Alcance v1: navegación local determinística, sin red, sin LLM, sin escrituras ni migraciones sobre la base de OpenCode.
- Fuera de alcance actual: búsqueda por árbol de directorios, edición de sesiones, compatibilidad garantizada con futuros esquemas internos de OpenCode, exportación avanzada o resúmenes generativos.

## Arquitectura del producto

```text
cwd actual
  └─ cli.py resuelve Path.cwd().resolve()
      └─ OpenCodeCli descubre DB con opencode db path
          └─ SQLiteSessionRepository lee session/message/part en modo read-only
                  └─ SessionNavigator transforma registros en filas de dominio y deriva raíz/todas
                  └─ SessionNavigatorApp renderiza, filtra y lanza opencode --session <id>
```

Límites principales:

| Capa | Responsabilidad | Archivos |
|---|---|---|
| Dominio | Modelos de fila, placeholders, matching y contexto fecha/id. | `src/opencode_session_navigator/domain.py` |
| Aplicación | Carga desde repositorio, estado de lista, filtro en memoria y preservación de selección. | `src/opencode_session_navigator/application.py` |
| Texto | Normalización, sanitización ANSI/control, truncado y derivación de descripción/resumen. | `src/opencode_session_navigator/text.py` |
| Infraestructura | CLI de OpenCode, launcher interactivo y repositorio SQLite read-only. | `src/opencode_session_navigator/infra/*.py` |
| TUI | Widgets Textual, bindings, mensajes de estado/error y handoff a OpenCode. | `src/opencode_session_navigator/tui.py` |

Mantené estos límites: la TUI no debe conocer SQL, el repositorio no debe conocer widgets, y las heurísticas de texto deben seguir testeables sin terminal ni SQLite real.

## Archivos clave

- `README.md`: uso para personas usuarias y contrato público de idioma.
- `pyproject.toml`: packaging Hatchling, entry point, dependencias y configuración de `pytest`, `ruff` y `mypy` strict.
- `.github/workflows/ci.yml`: workflow `CI`, job/check `ci`, requerido para gobernanza de `main`.
- `openspec/config.yaml`: configuración SDD/OpenSpec; `strict_tdd: false`, presupuesto de revisión 400 líneas, comandos de calidad.
- `openspec/specs/session-navigator/spec.md`: especificación vigente del navegador de sesiones.
- `openspec/changes/archive/2026-06-16-opencode-session-navigator/`: propuesta, diseño, tareas y verificación archivadas del cambio inicial.
- `tests/`: pruebas por capa; usan fakes y SQLite temporal, no deben lanzar OpenCode real.

## Stack y comandos

| Área | Herramienta |
|---|---|
| Lenguaje | Python 3.12+ |
| UI terminal | Textual |
| Base local | SQLite de OpenCode, acceso read-only |
| Gestión | `uv` |
| Packaging | `pyproject.toml` + Hatchling |
| Tests | `pytest` |
| Lint/formato | Ruff |
| Tipado | `mypy` strict |

Comandos habituales:

```bash
uv sync --dev
uv run opencode-session-navigator
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy
```

Antes de marcar una tarea como lista, ejecutá como mínimo:

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy
```

## Contratos de datos

- La base SQLite de OpenCode es un contrato interno de otro producto: tratala como inestable y leela defensivamente.
- El path de DB se obtiene con `opencode db path`; no hardcodear ubicaciones locales.
- Abrir SQLite con URI `file:{quote(str(path))}?mode=ro` y `uri=True`. No escribir, no migrar, no crear tablas auxiliares.
- Filtrar sesiones por igualdad exacta contra `Path.cwd().resolve()` y `session.directory = ?`. No incluir padres, subdirectorios ni paths relativos salvo que una spec futura lo cambie.
- Validar tablas/columnas requeridas antes de consultar y transformar errores en mensajes legibles.
- Ignorar JSON inválido, partes desconocidas o tipos no soportados si queda texto válido utilizable.
- Normalizar y sanitizar texto antes de mostrar o buscar: quitar secuencias ANSI/OSC, caracteres de control y espacios redundantes.

## Contratos de UX/TUI

- Textual es la interfaz principal; la lógica testeable debe vivir en controlador/estado y no solo en callbacks de widgets.
- Búsqueda: filtra en memoria por título, descripción y resumen normalizados juntos. En modo raíces evalúa todas las sesiones del `cwd` exacto y puede mostrar hijas coincidentes con su raíz contextual seleccionable.
- Vista: iniciar en raíces (`parent_id IS NULL`); `Ctrl+T` alterna a todas las sesiones agrupadas por raíz, con huérfanas visibles e identificadas.
- Selección: preservar `selected_id` si sigue visible; si no, seleccionar el primer resultado visible; si no hay resultados, no seleccionar nada.
- Navegación: flechas y `j`/`k` mueven la selección; `Enter` abre; `r` recarga; `q`/`Esc` salen.
- Apertura: ejecutar `opencode --session <id>` como proceso interactivo con argv seguro, no como string de shell.
- Handoff/restauración: al abrir una sesión, suspender la TUI cuando Textual lo soporte; al volver, recargar preservando filtro y selección. Si OpenCode sale con código no cero, informar el código y conservar contexto.
- Tests de TUI: preferir `app.run_test()` y fakes; recordá que una prueba Textual no reemplaza una revisión manual en terminal real para comportamiento visual/interactivo.

## Convenciones del proyecto

- Documentación, comentarios y docstrings del proyecto: español neutral/profesional.
- Identificadores, comandos, paquetes, rutas, nombres de archivo y APIs: conservar inglés técnico o el nombre exacto que corresponda.
- Commits: usar Conventional Commits en inglés cuando el usuario pida commitear. No agregar atribución de IA ni `Co-Authored-By`.
- Mantener diffs chicos y revisables. El presupuesto de revisión configurado es 400 líneas.
- No commitear, pushear, crear PRs ni tocar archivos no relacionados salvo pedido explícito.
- Si se cambian contratos, actualizar tests y documentación relacionada (`README.md`, `AGENTS.md`, OpenSpec si aplica).

## Flujo seguro para agentes

1. Inspeccionar `git status --short` y no pisar cambios existentes.
2. Leer `README.md`, `pyproject.toml`, la spec vigente y, si aplica, el diseño archivado relevante junto con los archivos de la capa afectada.
3. Preferir tests primero o TDD práctico para cambios de comportamiento; en este repo `strict_tdd` está desactivado, pero los tests son obligatorios.
4. Respetar límites de arquitectura: dominio/aplicación/infra/TUI.
5. Ejecutar los comandos de verificación completos antes de reportar éxito.
6. Revisar `git diff` para asegurar que solo cambió lo pedido.
7. Guardar en Engram descubrimientos importantes, gotchas o convenciones nuevas del proyecto.

## CI y gobernanza del repositorio

- Repositorio público: `balerdis/opencode-sessions`.
- `main` está protegido; el check requerido se llama `ci` y lo ejecuta GitHub Actions.
- CI corre en pull requests y pushes a `main`: instalación con `uv sync --dev`, `pytest`, `ruff check`, `ruff format --check` y `mypy`.
- No saltar hooks, checks ni protección de rama. Si un check falla, corregir la causa en lugar de ocultar el problema.

## Gotchas conocidos

- `gentle-ai` puede detectar falsos positivos en verificaciones si una línea contiene patrones como `Success: no...`; redactá reportes de verificación evitando frases ambiguas cuando sea relevante.
- La sanitización de metadatos locales importa: las sesiones pueden contener rutas, prompts, resúmenes o información sensible. No publicar dumps de SQLite ni logs sin revisarlos.
- SQLite de OpenCode es interno: futuras versiones pueden cambiar tablas o JSON. La respuesta correcta es degradar con errores legibles, no asumir estabilidad.
- Las pruebas de Textual cubren estado y bindings, pero algunos detalles de suspensión/restauración dependen del terminal real.
- El resumen actual es heurístico y barato: último texto útil de assistant, con fallback determinístico. No introducir llamadas a LLM o servicios externos sin spec nueva.

## Cómo agregar cambios futuros

- Empezá por el contrato: actualizá OpenSpec o al menos escribí tests que expresen el comportamiento esperado.
- Para nuevas fuentes de datos, extendé infraestructura y mantené el dominio independiente del esquema concreto.
- Para nuevas interacciones TUI, agregá primero comportamiento en `TuiSessionController` cuando sea posible y cubrilo con fakes.
- Si ampliás búsqueda o filtros, documentá si sigue siendo igualdad exacta por `cwd` o si cambia el alcance.
- Si cambiás comandos, tooling o convenciones, actualizá este archivo y el `README.md` en el mismo work unit.
