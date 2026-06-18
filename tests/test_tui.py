from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path

from textual.widgets import DataTable, Footer, Static

from opencode_session_navigator.application import SessionListState, SessionViewMode
from opencode_session_navigator.domain import SessionRow
from opencode_session_navigator.infra.opencode_cli import OpenCodeCliError
from opencode_session_navigator.tui import (
    SessionNavigatorApp,
    TuiSessionController,
    describe_state,
    selected_index_or_none,
    selected_row,
)


def test_controlador_carga_estado_vacio_con_mensaje_accionable() -> None:
    controller = TuiSessionController(
        loader=FakeLoader(()),
        launcher=FakeLauncher(),
        cwd=Path("/repo"),
    )

    controller.load()

    assert controller.state.visible_sessions == ()
    assert "No hay sesiones" in controller.status_message
    assert "/repo" in controller.status_message


def test_controlador_filtra_y_navega_sin_reconsultar_sqlite() -> None:
    loader = FakeLoader(
        (
            make_row("a", description="pytest"),
            make_row("b", description="sqlite pytest"),
        )
    )
    controller = TuiSessionController(loader=loader, launcher=FakeLauncher(), cwd=Path("/repo"))
    controller.load(selected_id="a")

    controller.apply_query("sqlite")
    controller.move_selection(1)

    selected = selected_row(controller.state)
    assert loader.calls == [(Path("/repo"), "", "a", SessionViewMode.ROOTS)]
    assert [row.id for row in controller.state.visible_sessions] == ["b"]
    assert selected is not None
    assert selected.id == "b"
    assert selected_index_or_none(controller.state) == 0


def test_controlador_abre_sesion_y_restaurar_filtro_y_seleccion() -> None:
    loader = FakeLoader(
        (
            make_row("a", description="python"),
            make_row("b", description="sqlite"),
        )
    )
    launcher = FakeLauncher()
    controller = TuiSessionController(loader=loader, launcher=launcher, cwd=Path("/repo"))
    controller.load()
    controller.apply_query("sqlite")

    returncode = controller.open_selected()

    assert returncode == 0
    assert launcher.launched_ids == ["b"]
    assert loader.calls[-1] == (Path("/repo"), "sqlite", "b", SessionViewMode.ROOTS)
    assert [row.id for row in controller.state.visible_sessions] == ["b"]
    assert controller.state.selected_id == "b"


def test_controlador_reporta_fallo_de_carga_con_mensaje_legible() -> None:
    controller = TuiSessionController(
        loader=FailingLoader(OpenCodeCliError("opencode db path falló")),
        launcher=FakeLauncher(),
        cwd=Path("/repo"),
    )

    controller.load(query="sqlite", selected_id="b")

    assert controller.state.visible_sessions == ()
    assert controller.state.query == "sqlite"
    assert controller.error_message is not None
    assert "No se pudieron cargar las sesiones" in controller.error_message
    assert "opencode db path falló" in controller.error_message
    assert "OpenCode" in controller.status_message


def test_controlador_reporta_error_del_launcher_y_conserva_estado() -> None:
    controller = TuiSessionController(
        loader=FakeLoader((make_row("a"),)),
        launcher=FakeLauncher(error=OpenCodeCliError("no existe opencode")),
        cwd=Path("/repo"),
    )
    controller.load()

    returncode = controller.open_selected()

    assert returncode is None
    assert controller.state.selected_id == "a"
    assert "No se pudo abrir la sesión a" in controller.status_message
    assert "no existe opencode" in controller.status_message


def test_controlador_reporta_oserror_del_launcher_y_conserva_estado() -> None:
    controller = TuiSessionController(
        loader=FakeLoader((make_row("a"),)),
        launcher=FakeLauncher(error=OSError("terminal no disponible")),
        cwd=Path("/repo"),
    )
    controller.load()

    returncode = controller.open_selected()

    assert returncode is None
    assert controller.state.selected_id == "a"
    assert "terminal no disponible" in controller.status_message


def test_controlador_reporta_codigo_no_cero_y_restaura_estado() -> None:
    loader = FakeLoader((make_row("a", description="python"), make_row("b", description="sqlite")))
    controller = TuiSessionController(
        loader=loader,
        launcher=FakeLauncher(returncode=7),
        cwd=Path("/repo"),
    )
    controller.load()
    controller.apply_query("sqlite")

    returncode = controller.open_selected()

    assert returncode == 7
    assert loader.calls[-1] == (Path("/repo"), "sqlite", "b", SessionViewMode.ROOTS)
    assert controller.state.selected_id == "b"
    assert "código 7" in controller.status_message
    assert "se recargó la TUI" in controller.status_message
    assert "filtro y la selección restaurados" in controller.status_message
    assert "lista anterior" not in controller.status_message


def test_controlador_conserva_error_visible_si_falla_recarga_despues_de_opencode() -> None:
    loader = FakeLoader((make_row("a", description="python"),))
    controller = TuiSessionController(
        loader=loader,
        launcher=FakeLauncher(),
        cwd=Path("/repo"),
    )
    controller.load()
    loader.error = OpenCodeCliError("opencode db path falló al volver")

    returncode = controller.open_selected()

    assert returncode == 0
    assert loader.calls[-1] == (Path("/repo"), "", "a", SessionViewMode.ROOTS)
    assert controller.error_message is not None
    assert "opencode db path falló al volver" in controller.error_message
    assert "OpenCode" in controller.status_message
    assert controller.status_message != "Sesión restaurada: a"


def test_app_textual_filtra_navega_con_flechas_y_abre_con_enter() -> None:
    async def run_app() -> None:
        launcher = FakeLauncher()
        controller = TuiSessionController(
            loader=FakeLoader(
                (
                    make_row("a", description="python"),
                    make_row("b", description="sqlite"),
                    make_row("c", description="sqlite logs"),
                )
            ),
            launcher=launcher,
            cwd=Path("/repo"),
        )
        app = SessionNavigatorApp(controller)

        async with app.run_test() as pilot:
            await pilot.press("s", "q", "l")
            await pilot.pause()
            await pilot.press("down")
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()

        assert controller.state.query == "sql"
        assert [row.id for row in controller.state.visible_sessions] == ["b", "c"]
        assert launcher.launched_ids == ["c"]
        assert controller.state.selected_id == "c"
        assert controller.status_message == "Sesión restaurada: c"

    asyncio.run(run_app())


def test_app_textual_muestra_ayuda_de_ctrl_t_y_footer() -> None:
    async def run_app() -> None:
        controller = TuiSessionController(
            loader=FakeLoader((make_row("raiz", title="Raíz"),)),
            launcher=FakeLauncher(),
            cwd=Path("/repo"),
        )
        app = SessionNavigatorApp(controller)

        async with app.run_test() as pilot:
            await pilot.pause()
            status = app.query_one("#status", Static)
            footer = app.query_one(Footer)

            assert "Ctrl+T alterna raíces/todas" in str(status.content)
            assert footer.display
            assert any(
                getattr(binding, "key", None) == "ctrl+t"
                and getattr(binding, "description", None) == "Raíz/todas"
                for binding in app.BINDINGS
            )

    asyncio.run(run_app())


def test_app_textual_renderiza_prefijos_de_arbol_en_tabla() -> None:
    async def run_app() -> None:
        controller = TuiSessionController(
            loader=FakeLoader(
                (
                    make_row("raiz", title="Raíz"),
                    make_row("hija-a", title="Hija A", parent_id="raiz"),
                    make_row("hija-b", title="Hija B", parent_id="raiz"),
                )
            ),
            launcher=FakeLauncher(),
            cwd=Path("/repo"),
        )
        app = SessionNavigatorApp(controller)

        async with app.run_test() as pilot:
            await pilot.press("ctrl+t")
            await pilot.pause()
            table = app.query_one("#sessions", DataTable)

            assert table.row_count == 3
            assert [table.get_row_at(index)[0] for index in range(table.row_count)] == [
                "Raíz",
                "└─ Hija A",
                "└─ Hija B",
            ]

    asyncio.run(run_app())


def test_controlador_alterna_modo_y_preserva_seleccion_visible() -> None:
    controller = TuiSessionController(
        loader=FakeLoader(
            (
                make_row("raiz", title="Raíz"),
                make_row("hija", title="Hija", parent_id="raiz"),
            )
        ),
        launcher=FakeLauncher(),
        cwd=Path("/repo"),
    )
    controller.load()

    controller.toggle_view_mode()

    assert controller.state.view_mode == SessionViewMode.ALL
    assert [row.id for row in controller.state.visible_sessions] == ["raiz", "hija"]
    assert controller.state.selected_id == "raiz"
    assert "modo todas" in controller.status_message


def test_controlador_abre_raiz_contextual_real() -> None:
    launcher = FakeLauncher()
    controller = TuiSessionController(
        loader=FakeLoader(
            (
                make_row("raiz", title="Raíz", description="sin match"),
                make_row("hija", title="Hija", description="sqlite", parent_id="raiz"),
            )
        ),
        launcher=launcher,
        cwd=Path("/repo"),
    )
    controller.load()
    controller.apply_query("sqlite")

    returncode = controller.open_selected()

    assert returncode == 0
    assert launcher.launched_ids == ["raiz"]


def test_describe_state_reporta_sin_resultados() -> None:
    state = SessionListState.from_sessions((make_row("a"),)).with_query("no-match")

    assert "Sin resultados" in describe_state(Path("/repo"), state)


@dataclass
class FakeLoader:
    rows: tuple[SessionRow, ...]
    calls: list[tuple[Path, str, str | None, SessionViewMode]] = field(default_factory=list)
    error: Exception | None = None

    def load(
        self,
        cwd: Path,
        *,
        query: str = "",
        selected_id: str | None = None,
        view_mode: SessionViewMode = SessionViewMode.ROOTS,
    ) -> SessionListState:
        self.calls.append((cwd, query, selected_id, view_mode))
        if self.error is not None:
            raise self.error
        return SessionListState.from_sessions(
            self.rows, query=query, selected_id=selected_id, view_mode=view_mode
        )


@dataclass
class FailingLoader:
    error: Exception

    def load(
        self,
        cwd: Path,
        *,
        query: str = "",
        selected_id: str | None = None,
        view_mode: SessionViewMode = SessionViewMode.ROOTS,
    ) -> SessionListState:
        raise self.error


@dataclass
class FakeLauncher:
    launched_ids: list[str] = field(default_factory=list)
    returncode: int = 0
    error: Exception | None = None

    def launch_session(self, session_id: str) -> int:
        if self.error is not None:
            raise self.error
        self.launched_ids.append(session_id)
        return self.returncode


def make_row(
    session_id: str,
    *,
    title: str = "Título",
    description: str = "Descripción",
    summary: str = "Resumen",
    parent_id: str | None = None,
) -> SessionRow:
    return SessionRow.create(
        session_id=session_id,
        title=title,
        description=description,
        summary=summary,
        updated_at=None,
        parent_id=parent_id,
    )
