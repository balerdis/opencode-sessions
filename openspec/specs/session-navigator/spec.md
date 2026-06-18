# Especificación: Navegador de sesiones

## Propósito

TUI Textual para listar, buscar y reabrir sesiones locales de OpenCode del cwd exacto, leyendo SQLite en solo lectura.

## Requirements

### Requirement: Filtrado por cwd exacto

El sistema MUST resolver `Path.cwd().resolve()` y MUST listar solo sesiones donde `session.directory` coincide exactamente. MUST NOT incluir padres, subdirectorios ni coincidencias por `path` relativo en v1.

#### Scenario: Lista exacta
- GIVEN cwd `/repo/app` y sesiones en `/repo/app`, `/repo` y `/repo/app/sub`
- WHEN se carga el navegador
- THEN solo aparece `/repo/app`

#### Scenario: Lista vacía
- GIVEN un cwd sin sesiones coincidentes
- WHEN se carga el navegador
- THEN muestra el cwd detectado y un mensaje accionable

### Requirement: Descubrimiento y lectura defensiva de DB

El sistema MUST obtener la DB con `opencode db path`, abrirla en solo lectura y MUST NOT escribir ni migrar. Ante DB ausente, inaccesible o esquema faltante, MUST mostrar error legible sin traceback crudo.

#### Scenario: DB válida
- GIVEN `opencode db path` devuelve una DB compatible
- WHEN se cargan sesiones
- THEN se abre en solo lectura
- AND no hay escrituras

#### Scenario: Esquema incompatible
- GIVEN falta una tabla o columna requerida
- WHEN se cargan sesiones
- THEN informa incompatibilidad de esquema
- AND permite salir de la TUI

### Requirement: Metadatos de sesión

El sistema MUST construir cada fila con id, título, contexto fecha/id, descripción y resumen. SHOULD usar `message` + `part` como fuente v1. Si faltan datos, MUST usar placeholders claros.

#### Scenario: Datos completos
- GIVEN título, timestamp, texto de usuario y texto de asistente
- WHEN se arma la fila
- THEN muestra título, fecha/id, descripción y resumen

#### Scenario: Datos parciales
- GIVEN una sesión sin título ni textos útiles
- WHEN se arma la fila
- THEN muestra placeholders legibles

### Requirement: Descripción y resumen v1

El sistema MUST truncar descripciones que excedan el límite visual y terminarlas en `...`. El resumen MUST ser heurístico, determinístico y barato; MUST NOT usar LLM ni servicios externos.

#### Scenario: Descripción larga
- GIVEN una descripción mayor al límite
- WHEN se renderiza la fila
- THEN se acorta y termina en `...`

#### Scenario: Sin texto de asistente
- GIVEN una sesión sin texto de asistente útil
- WHEN se genera el resumen
- THEN deriva un resumen desde datos disponibles o muestra placeholder

### Requirement: Búsqueda interactiva

El sistema MUST filtrar en la TUI sobre título, descripción y resumen normalizados juntos. El filtro MUST operar en memoria y SHOULD preservar selección si el ítem sigue visible.

#### Scenario: Coincidencia fuera del título
- GIVEN una consulta presente solo en descripción o resumen
- WHEN el usuario escribe la consulta
- THEN la sesión aparece en resultados

#### Scenario: Selección preservada
- GIVEN una sesión seleccionada que sigue visible tras filtrar
- WHEN cambia la consulta
- THEN permanece seleccionada

### Requirement: Navegación, apertura y restauración

El sistema MUST permitir navegación por teclado. Al confirmar, MUST ejecutar `opencode --session <id>` como proceso interactivo, ceder la terminal y restaurar lista, filtro y selección al terminar.

#### Scenario: Abrir sesión
- GIVEN una sesión visible seleccionada
- WHEN el usuario confirma
- THEN se ejecuta `opencode --session <id>` con ese id

#### Scenario: Volver a la TUI
- GIVEN filtro y selección activos antes de abrir
- WHEN OpenCode termina
- THEN la TUI vuelve con el mismo filtro, lista visible y selección

### Requirement: Resiliencia del contrato interno

El sistema MUST tratar SQLite de OpenCode como contrato interno. Ante JSON inesperado, partes desconocidas o tablas futuras no usadas, SHOULD ignorar lo no soportado y MUST degradar de forma utilizable.

#### Scenario: Partes desconocidas
- GIVEN partes desconocidas mezcladas con texto válido
- WHEN se extraen descripción y resumen
- THEN se ignoran las partes desconocidas
- AND se usa el texto válido

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
