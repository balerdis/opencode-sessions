# OpenCode Session Navigator

Una TUI para listar, buscar y reabrir sesiones locales de OpenCode asociadas al directorio actual.

El objetivo del proyecto es resolver una situación muy concreta: cuando trabajás con varias sesiones de OpenCode, necesitás encontrar rápido la sesión correcta del proyecto en el que estás parado y volver a abrirla sin buscar IDs manualmente.

## Qué hace

- Descubre la base local de OpenCode usando `opencode db path`.
- Lee la base SQLite en modo solo lectura.
- Lista únicamente las sesiones cuyo `session.directory` coincide exactamente con el directorio actual.
- Muestra por defecto solo sesiones raíz y permite alternar a todas las sesiones agrupadas por raíz.
- Permite filtrar por título, descripción o resumen.
- Reabre la sesión seleccionada con `opencode --session <id>`.

## Stack tecnológico

| Área | Tecnología |
|------|------------|
| Lenguaje | Python 3.12 |
| UI terminal | Textual |
| Base de datos | SQLite, leyendo la base local de OpenCode |
| Packaging | `pyproject.toml` + Hatchling |
| Entorno y comandos | uv |
| Tests | pytest |
| Lint y formato | Ruff |
| Tipado | mypy en modo strict |

## Arquitectura

El proyecto está separado por responsabilidades para mantener la TUI, la lógica de aplicación y la infraestructura desacopladas.

```text
src/opencode_session_navigator/
├── cli.py                  # Punto de entrada del comando
├── tui.py                  # App Textual, controller y acciones de teclado
├── application.py          # Construcción del estado filtrado de sesiones
├── domain.py               # Modelos y reglas de matching
├── text.py                 # Normalización y truncado de texto
└── infra/
    ├── opencode_cli.py     # Wrapper del CLI de OpenCode
    └── sqlite_repo.py      # Lectura read-only de la DB SQLite
```

Flujo principal:

1. `cli.py` toma el directorio actual con `Path.cwd().resolve()`.
2. `OpenCodeCli` descubre la base de OpenCode.
3. `sqlite_repo.py` lee las sesiones en modo solo lectura.
4. `application.py` arma el estado visible, aplica el filtro y deriva la vista raíz/todas.
5. `tui.py` muestra la interfaz y lanza `opencode --session <id>` al presionar `Enter`.

## Requisitos

- Python 3.12 o superior.
- `uv` instalado.
- OpenCode instalado y disponible como comando `opencode`.
- Tener sesiones locales de OpenCode creadas previamente.

## Instalación para desarrollo

Cloná el repositorio e instalá las dependencias:

```bash
git clone https://github.com/balerdis/opencode-sessions.git
cd opencode-sessions
uv sync --dev
```

Verificá que todo esté correcto:

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy
```

## Uso

Desde el directorio del proyecto cuyas sesiones querés navegar:

```bash
uv run opencode-session-navigator
```

Controles principales:

| Acción | Tecla |
|--------|-------|
| Filtrar sesiones | Escribir en el buscador |
| Mover selección | `↑` / `↓` |
| Mover selección sin foco de texto | `j` / `k` |
| Abrir sesión seleccionada | `Enter` |
| Recargar sesiones | `r` |
| Alternar raíces / todas | `Ctrl+T` |
| Salir | `q` o `Esc` |

La vista inicial muestra sesiones raíz (`parent_id IS NULL`) para reducir ruido de sub-sesiones de agentes. Si una búsqueda coincide solo con una sub-sesión, tanto en vista raíz como en vista “todas” la TUI muestra su raíz disponible inmediatamente arriba como contexto real: esa fila se puede seleccionar y abrir igual que cualquier sesión. Con `Ctrl+T` podés alternar a la vista “todas”, donde las sub-sesiones aparecen debajo de su raíz y las huérfanas quedan identificadas.

Cuando abrís una sesión, la TUI ejecuta OpenCode. Al salir de OpenCode, vuelve a la interfaz restaurando el filtro, el modo de vista y la selección cuando la sesión sigue visible.

## Seguridad y privacidad

La herramienta está pensada para trabajar sobre datos locales de OpenCode con el menor impacto posible:

- Abre la base SQLite con `mode=ro`.
- No ejecuta migraciones.
- No escribe sobre la base de OpenCode.
- No lista sesiones de otros directorios: filtra por coincidencia exacta con el directorio actual resuelto.
- Limpia caracteres ANSI/control antes de mostrar o buscar texto de sesiones.

Importante: las sesiones de OpenCode pueden contener rutas locales, prompts, resúmenes o información sensible. Revisá qué archivos y artefactos publicás si compartís capturas, logs o datos derivados de sesiones.

## Estado del proyecto

Este es un proyecto inicial. Hoy cubre el flujo principal de navegación local de sesiones y mantiene tests para la lógica de aplicación, texto, infraestructura y TUI.

## Contrato de idioma

La documentación y los comentarios del proyecto se escriben en español. Los identificadores de código y nombres estándar del ecosistema pueden mantenerse en inglés cuando sea convencional.
