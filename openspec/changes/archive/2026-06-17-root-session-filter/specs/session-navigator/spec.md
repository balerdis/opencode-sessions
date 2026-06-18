# Delta para session-navigator

## ADDED Requirements

### Requirement: Metadatos jerárquicos de sesión

El sistema MUST conservar `session.parent_id` desde SQLite hasta las filas visibles. Una sesión raíz MUST identificarse por `parent_id IS NULL`. La jerarquía MUST calcularse únicamente dentro del conjunto ya filtrado por `session.directory = Path.cwd().resolve()`.

#### Scenario: Conserva raíz e hija del cwd exacto
- GIVEN una raíz con `parent_id IS NULL` y una hija con `parent_id` igual al id de la raíz en el cwd actual
- WHEN se cargan las sesiones
- THEN ambas filas conservan su id y su relación padre/hija

#### Scenario: No cruza límites de cwd
- GIVEN una hija del cwd actual cuyo padre pertenece a otro directorio
- WHEN se construye la jerarquía visible
- THEN el padre externo no aparece
- AND la hija se trata según las reglas de huérfanos

#### Scenario: Columna requerida ausente
- GIVEN la tabla `session` no expone `parent_id`
- WHEN se cargan sesiones
- THEN se informa incompatibilidad de esquema de forma legible

### Requirement: Vista raíz por defecto y búsqueda contextual

El sistema MUST iniciar en modo raíz y mostrar solo sesiones con `parent_id IS NULL`. En modo raíz, la búsqueda MUST evaluar todas las sesiones del cwd exacto y MAY mostrar hijas coincidentes con su raíz contextual disponible.

#### Scenario: Inicio muestra solo raíces
- GIVEN raíces e hijas del cwd actual
- WHEN se abre la TUI sin consulta
- THEN solo aparecen las raíces

#### Scenario: Búsqueda encuentra hija oculta
- GIVEN una hija contiene la consulta y su raíz no coincide
- WHEN el usuario busca en modo raíz
- THEN aparece la raíz inmediatamente antes de la hija
- AND aparece la hija coincidente

#### Scenario: Raíz contextual es real
- GIVEN una raíz contextual visible por coincidencia de una hija
- WHEN el usuario la selecciona y confirma
- THEN se ejecuta `opencode --session <root_id>`

### Requirement: Modo todas las sesiones

El sistema MUST ofrecer un modo “todas” que muestre raíces agrupadas con sus hijas debajo en presentación tipo árbol. Las raíces SHOULD ordenarse por recencia y sus hijas SHOULD permanecer bajo su raíz. Con una búsqueda activa, si solo coincide una hija/sub-sesión, su raíz disponible MUST permanecer visible inmediatamente antes como contexto real seleccionable y abrible. Las hijas sin raíz disponible MUST seguir visibles como huérfanas.

#### Scenario: Agrupa raíz e hijas
- GIVEN una raíz con dos hijas del cwd actual
- WHEN el usuario activa modo “todas”
- THEN la raíz aparece como contenedor visual
- AND sus hijas aparecen debajo con indicador jerárquico

#### Scenario: Muestra huérfanas
- GIVEN una hija cuyo `parent_id` no corresponde a ninguna raíz cargada
- WHEN el usuario activa modo “todas”
- THEN la hija aparece como huérfana identificable

#### Scenario: Búsqueda conserva raíz contextual
- GIVEN una hija contiene la consulta y su raíz no coincide
- WHEN el usuario busca en modo “todas”
- THEN aparece la raíz inmediatamente antes de la hija
- AND aparece la hija coincidente

### Requirement: Alternancia y selección estable

El sistema MUST exponer un atajo de teclado para alternar modo raíz/todas y MUST mostrarlo en la barra inferior o ayuda. Al cambiar modo, buscar o volver desde OpenCode, la selección SHOULD preservarse si la misma sesión sigue visible; de lo contrario, SHOULD moverse al primer resultado visible.

#### Scenario: Atajo visible
- GIVEN la TUI cargada
- WHEN se renderiza la ayuda inferior
- THEN muestra el atajo para alternar raíz/todas

#### Scenario: Preserva selección visible
- GIVEN una sesión seleccionada que sigue visible tras cambiar modo o consulta
- WHEN cambia el modo o la búsqueda
- THEN esa sesión permanece seleccionada

#### Scenario: Reubica selección oculta
- GIVEN una hija seleccionada en modo “todas”
- WHEN el usuario vuelve a modo raíz sin una búsqueda que muestre esa hija
- THEN la selección pasa al primer resultado visible
