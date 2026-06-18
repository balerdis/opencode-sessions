## Exploración: root-session-filter

### Estado actual
- La TUI carga sesiones del `cwd` exacto y muestra todas las filas que devuelve SQLite.
- El repositorio local filtra solo por `session.directory = ?`; hoy no distingue `parent_id`.
- `SessionRow` no conserva `parent_id`, así que la capa de aplicación ya perdió la información jerárquica.
- La búsqueda actual filtra en memoria por título, descripción y resumen normalizados.
- El listado se ordena por `time_updated DESC`, sin agrupación por árbol.

### Hallazgos clave
- En el schema upstream de OpenCode, `session.parent_id` existe y es nullable.
- OpenCode crea sesiones hijas pasando `parentID`; la API oficial soporta `roots: true` para listar solo raíces.
- En el código upstream, la UI de sesiones filtra explícitamente `parentID === undefined` para construir la vista raíz.
- En la DB local validada, `session` tiene `parent_id`; para este `cwd` hay 53 sesiones: 2 raíces y 51 hijas.
- No se detectaron huérfanos (`parent_id` apuntando a una sesión inexistente) en la DB local.

### Áreas afectadas
- `src/opencode_session_navigator/infra/sqlite_repo.py` — necesita exponer `parent_id` o una señal equivalente para filtrar raíces.
- `src/opencode_session_navigator/application.py` — debe incorporar el modo de vista (raíces / todas) y preservar selección con ese filtro.
- `src/opencode_session_navigator/domain.py` — `SessionRow` hoy no modela jerarquía; habría que ampliarlo o agregar metadata derivada.
- `src/opencode_session_navigator/tui.py` — necesita toggle de vista, recarga y render de prefijos jerárquicos cuando se muestren hijas.
- `tests/` — faltan casos para modo raíz por defecto, modo “ver todo” y prefijos/orden jerárquico.
- `README.md` y `openspec/specs/session-navigator/spec.md` — deben documentar el nuevo comportamiento visible.

### Enfoques
1. **Filtro de vista en la aplicación** — cargar todo siempre y filtrar raíces en memoria por `parent_id`.
   - Pros: cambio pequeño; no toca mucho el repositorio.
   - Contras: trae más filas de las necesarias; la jerarquía sigue sin existir en el modelo de dominio.
   - Esfuerzo: Bajo

2. **Filtro de raíces en el repositorio + modo de vista explícito** — pasar `roots=True/False` desde la TUI y recargar al alternar.
   - Pros: usa el contrato real de OpenCode (`parent_id` / `roots`); reduce carga cuando la vista por defecto es raíz.
   - Contras: agrega branching en infraestructura y estado de UI.
   - Esfuerzo: Medio

3. **Vista jerárquica completa** — además del filtro, ordenar por árbol y prefijar hijos con `|_` / `├─` según profundidad.
   - Pros: mejor encaje con la intención del usuario cuando quiere ver subagentes.
   - Contras: más lógica de ordenamiento, selección y pruebas; puede quedar raro si el árbol se mezcla con orden por recencia.
   - Esfuerzo: Medio/Alto

### Recomendación
Ir con **(2)** como base y sumar **prefijo jerárquico derivado** para la vista “ver todo”. El contrato upstream ya distingue raíces con `parent_id IS NULL`, así que ese debería ser el criterio canónico. Para la primera iteración, mantener el orden por recencia y mostrar prefijos en el título; si la lectura visual queda confusa, la siguiente iteración puede pasar a orden tipo árbol (DFS por raíz).

### Riesgos
- Definir mal “raíz” y mostrar sesiones huérfanas o hijos como raíces.
- Romper la preservación de selección al alternar entre raíz / todas.
- Si la vista “ver todo” mantiene recencia plana, el árbol puede verse intercalado y confuso.
- La semántica de búsqueda debe quedar explícita: hoy filtraría sobre el conjunto visible activo, no sobre todas las sesiones ocultas.

### Listo para propuesta
Sí. Hace falta una propuesta antes de implementar porque todavía hay decisiones de producto abiertas: semántica exacta de raíz, persistencia del modo de vista, comportamiento de búsqueda y nivel de jerarquía visual.
