import subprocess
from collections.abc import Sequence
from pathlib import Path

import pytest

from opencode_session_navigator.infra.opencode_cli import (
    OpenCodeCli,
    OpenCodeCliError,
    OpenCodeSessionLauncher,
    default_runner,
)


def test_db_path_resuelve_salida_del_cli(tmp_path: Path) -> None:
    db_path = tmp_path / "opencode.db"

    def runner(args: list[str]) -> subprocess.CompletedProcess[str]:
        assert args == ["opencode", "db", "path"]
        return subprocess.CompletedProcess(args, 0, stdout=f"{db_path}\n", stderr="")

    assert OpenCodeCli(runner=runner).db_path() == db_path.resolve()


def test_db_path_reporta_error_legible() -> None:
    def runner(args: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args, 1, stdout="", stderr="falló")

    with pytest.raises(OpenCodeCliError, match="No se pudo descubrir"):
        OpenCodeCli(runner=runner).db_path()


def test_default_runner_reporta_error_legible_si_falta_opencode() -> None:
    with pytest.raises(OpenCodeCliError, match="opencode.*no está disponible"):
        default_runner(["/ruta/inexistente/opencode", "db", "path"])


def test_session_command_valida_id() -> None:
    cli = OpenCodeCli()

    assert cli.session_command("ses_123") == ["opencode", "--session", "ses_123"]
    with pytest.raises(OpenCodeCliError, match="vacío"):
        cli.session_command(" ")


def test_launcher_ejecuta_sesion_con_argv_seguro() -> None:
    calls: list[list[str]] = []

    def runner(args: Sequence[str]) -> subprocess.CompletedProcess[bytes]:
        calls.append(list(args))
        return subprocess.CompletedProcess(list(args), 0)

    returncode = OpenCodeSessionLauncher(runner=runner).launch_session("ses_123")

    assert returncode == 0
    assert calls == [["opencode", "--session", "ses_123"]]
