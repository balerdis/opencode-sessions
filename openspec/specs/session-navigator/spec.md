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
