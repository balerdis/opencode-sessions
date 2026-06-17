from __future__ import annotations

from pathlib import Path

from opencode_session_navigator.infra.opencode_cli import OpenCodeCli, OpenCodeSessionLauncher
from opencode_session_navigator.tui import (
    DefaultSessionLoader,
    SessionNavigatorApp,
    TuiSessionController,
)


def main() -> int:
    """Ejecuta la TUI del navegador de sesiones."""
    cwd = Path.cwd().resolve()
    cli = OpenCodeCli()
    controller = TuiSessionController(
        loader=DefaultSessionLoader(cli),
        launcher=OpenCodeSessionLauncher(cli),
        cwd=cwd,
    )
    SessionNavigatorApp(controller).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
