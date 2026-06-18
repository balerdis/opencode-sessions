# Propuesta: Filtro de sesiones raíz

## Problema de producto

El navegador mezcla sesiones raíz con sub-sesiones de agentes en una lista plana por recencia. Eso conserva actualidad, pero genera ruido cuando la persona busca retomar la conversación principal del proyecto.

## Usuarios y situaciones

- Personas que reabren sesiones locales de OpenCode desde el `cwd` exacto.
- Situaciones con muchas sub-sesiones creadas por agentes donde la raíz es el punto natural de continuidad.
- Búsquedas donde una sub-sesión contiene información útil y necesita contexto de su raíz.

## Brecha actual

`session.parent_id` existe en OpenCode, pero `SessionRow` no lo conserva. La app solo filtra por `session.directory = ?` y ordena todo por `time_updated DESC`.

## Alcance

### Incluido
- Vista por defecto de sesiones raíz (`parent_id IS NULL`).
- Toggle de teclado visible en ayuda inferior para alternar raíz / todas.
- Búsqueda que puede mostrar sub-sesiones aunque el modo raíz esté activo.
- Raíz contextual sobre una sub-sesión coincidente, seleccionable y abrible.
- Modo “todas” agrupado por raíz con hijos debajo y huérfanos visibles.

### No incluido
- Persistir preferencia de modo entre ejecuciones.
- Expandir/colapsar ramas.
- Búsqueda por padres/subdirectorios.
- Escrituras o migraciones sobre la DB de OpenCode.

## Capacidades

### Nuevas capacidades
- Ninguna.

### Capacidades modificadas
- `session-navigator`: cambia el comportamiento visible de listado, búsqueda, selección y presentación jerárquica.

## Requisitos PRD

- Por defecto, la lista MUST mostrar raíces y ocultar hijos no coincidentes.
- La búsqueda MUST evaluar el conjunto del `cwd` y mostrar hijos coincidentes aun en modo raíz.
- Si un hijo coincide y su raíz disponible no coincide, la raíz MUST aparecer arriba como contexto real, seleccionable y abrible con `opencode --session <root_id>`.
- En modo “todas”, la vista MUST agrupar cada raíz con sus hijos debajo; hijos sin raíz disponible MUST seguir visibles como huérfanos.
- La selección SHOULD preservarse al filtrar, alternar modo o volver desde OpenCode si la sesión sigue visible.

## Flujos UX

1. Abrir TUI: ve raíces recientes, sin ruido de sub-agentes.
2. Buscar texto de una sub-sesión: aparece la raíz contextual y debajo el hijo coincidente.
3. Alternar “todas”: ve árbol raíz → hijos, con huérfanos separados/identificables.

## Enfoque

Propagar `parent_id` desde SQLite al dominio, mantener lectura read-only, aplicar modo de vista en aplicación/controlador y renderizar relación jerárquica en TUI sin convertir raíces contextuales en headers muertos.

## Áreas afectadas

| Área | Impacto | Descripción |
|---|---|---|
| `src/opencode_session_navigator/infra/sqlite_repo.py` | Modificado | Leer y validar `session.parent_id`. |
| `src/opencode_session_navigator/domain.py` | Modificado | Modelar jerarquía/orfandad. |
| `src/opencode_session_navigator/application.py` | Modificado | Filtrado, búsqueda global y orden agrupado. |
| `src/opencode_session_navigator/tui.py` | Modificado | Toggle, ayuda inferior y render tree-like. |
| `tests/`, `README.md`, `openspec/specs/session-navigator/spec.md` | Modificado | Cobertura y documentación del contrato. |

## Supuestos y límites de primera entrega

- Raíz significa `parent_id IS NULL`.
- No se soporta profundidad arbitraria más allá de agrupar por `parent_id`; si aparece, se degrada de forma legible.
- El modo inicial siempre es raíz.

## Riesgos

| Riesgo | Prob. | Mitigación |
|---|---:|---|
| Confundir contexto con header inerte | Media | Tests de selección/apertura sobre raíz contextual. |
| Orden jerárquico reduce recencia visible | Media | Mantener raíces por recencia y ordenar hijos dentro del grupo. |
| Esquema futuro cambia `parent_id` | Baja | Validación defensiva y error legible. |

## Plan de rollback

Revertir cambios de modelo, consulta, controlador y TUI; restaurar listado plano por `time_updated DESC` y quitar documentación/spec delta del cambio.

## Criterios de éxito

- [ ] Inicio muestra solo raíces del `cwd` exacto.
- [ ] Búsqueda encuentra hijos y muestra raíz contextual abrible.
- [ ] Modo “todas” agrupa raíz/hijos y no oculta huérfanos.
- [ ] Toggle figura en ayuda inferior y preserva selección cuando corresponde.
