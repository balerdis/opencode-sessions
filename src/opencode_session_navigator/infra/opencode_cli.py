from __future__ import annotations

import subprocess
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


class OpenCodeCliError(RuntimeError):
    """Error legible al invocar el CLI de OpenCode."""


class CommandRunner(Protocol):
    def __call__(self, args: list[str]) -> subprocess.CompletedProcess[str]: ...


class InteractiveRunner(Protocol):
    def __call__(self, args: Sequence[str]) -> subprocess.CompletedProcess[bytes]: ...


def default_runner(args: list[str]) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(args, check=False, capture_output=True, text=True)
    except FileNotFoundError as error:
        raise OpenCodeCliError(
            "No se pudo ejecutar OpenCode: el comando 'opencode' no está disponible."
        ) from error


def default_interactive_runner(args: Sequence[str]) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(list(args), check=False)
    except FileNotFoundError as error:
        raise OpenCodeCliError(
            "No se pudo ejecutar OpenCode: el comando 'opencode' no está disponible."
        ) from error


@dataclass(frozen=True)
class OpenCodeCli:
    runner: CommandRunner = default_runner

    def db_path(self) -> Path:
        result = self.runner(["opencode", "db", "path"])
        if result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip() or "sin detalle"
            raise OpenCodeCliError(f"No se pudo descubrir la base de OpenCode: {detail}")

        raw_path = result.stdout.strip()
        if not raw_path:
            raise OpenCodeCliError("OpenCode no devolvió una ruta de base de datos.")

        return Path(raw_path).expanduser().resolve()

    def session_command(self, session_id: str) -> list[str]:
        if not session_id.strip():
            raise OpenCodeCliError("El id de sesión está vacío.")
        return ["opencode", "--session", session_id]


@dataclass(frozen=True)
class OpenCodeSessionLauncher:
    cli: OpenCodeCli = field(default_factory=OpenCodeCli)
    runner: InteractiveRunner = default_interactive_runner

    def launch_session(self, session_id: str) -> int:
        result = self.runner(self.cli.session_command(session_id))
        return result.returncode
