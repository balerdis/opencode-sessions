from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from textual.app import App, ComposeResult, SuspendNotSupported
from textual.binding import Binding
from textual.widgets import DataTable, Footer, Header, Input, Static

from opencode_session_navigator.application import SessionListState, SessionNavigator
from opencode_session_navigator.domain import SessionRow
from opencode_session_navigator.infra.opencode_cli import OpenCodeCli, OpenCodeCliError
from opencode_session_navigator.infra.sqlite_repo import (
    SQLiteRepositoryError,
    SQLiteSessionRepository,
)


class SessionLoader(Protocol):
    def load(
        self,
        cwd: Path,
        *,
        query: str = "",
        selected_id: str | None = None,
    ) -> SessionListState: ...


class SessionLauncher(Protocol):
    def launch_session(self, session_id: str) -> int: ...


@dataclass(frozen=True)
class DefaultSessionLoader:
    cli: OpenCodeCli = field(default_factory=OpenCodeCli)

    def load(
        self,
        cwd: Path,
        *,
        query: str = "",
        selected_id: str | None = None,
    ) -> SessionListState:
        repository = SQLiteSessionRepository(self.cli.db_path())
        return SessionNavigator(repository).load(cwd, query=query, selected_id=selected_id)


@dataclass
class TuiSessionController:
    loader: SessionLoader
    launcher: SessionLauncher
    cwd: Path
    state: SessionListState = field(default_factory=lambda: SessionListState.from_sessions(()))
    status_message: str = "Cargando sesiones..."
    error_message: str | None = None

    def load(self, *, query: str = "", selected_id: str | None = None) -> None:
        try:
            self.state = self.loader.load(self.cwd, query=query, selected_id=selected_id)
        except (OpenCodeCliError, SQLiteRepositoryError, OSError) as error:
            self.error_message = f"No se pudieron cargar las sesiones: {error}"
            self.status_message = "Revisá que OpenCode esté instalado y que la base sea accesible."
            self.state = SessionListState.from_sessions((), query=query)
            return

        self.error_message = None
        self.status_message = describe_state(self.cwd, self.state)

    def apply_query(self, query: str) -> None:
        self.state = self.state.with_query(query)
        self.status_message = describe_state(self.cwd, self.state)

    def move_selection(self, offset: int) -> None:
        rows = self.state.visible_sessions
        if not rows:
            self.state = self.state.with_selected_id(None)
            return

        current_index = selected_index(self.state)
        next_index = min(max(current_index + offset, 0), len(rows) - 1)
        self.state = self.state.with_selected_id(rows[next_index].id)

    def open_selected(self) -> int | None:
        row = selected_row(self.state)
        if row is None:
            self.status_message = "No hay una sesión visible para abrir."
            return None

        query = self.state.query
        selected_id = row.id
        try:
            returncode = self.launcher.launch_session(selected_id)
        except (OpenCodeCliError, OSError) as error:
            self.status_message = f"No se pudo abrir la sesión {selected_id}: {error}"
            return None

        self.load(query=query, selected_id=selected_id)
        if self.error_message is not None:
            return returncode

        if returncode == 0:
            self.status_message = f"Sesión restaurada: {selected_id}"
        else:
            self.status_message = (
                f"OpenCode terminó con código {returncode}; se recargó la TUI "
                "con el filtro y la selección restaurados."
            )
        return returncode


class SessionNavigatorApp(App[None]):
    TITLE = "Navegador de sesiones de OpenCode"
    BINDINGS = [
        ("q", "quit", "Salir"),
        ("escape", "quit", "Salir"),
        Binding("down", "cursor_down", "Bajar", priority=True),
        Binding("up", "cursor_up", "Subir", priority=True),
        ("j", "cursor_down", "Bajar"),
        ("k", "cursor_up", "Subir"),
        Binding("enter", "open_selected", "Abrir", priority=True),
        ("r", "reload", "Recargar"),
    ]

    def __init__(self, controller: TuiSessionController) -> None:
        super().__init__()
        self.controller = controller

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(f"Directorio: {self.controller.cwd}", id="cwd")
        yield Input(placeholder="Buscar por título, descripción o resumen", id="search")
        yield Static("Cargando sesiones...", id="status")
        yield DataTable(id="sessions")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#sessions", DataTable)
        table.cursor_type = "row"
        table.add_columns("Título", "Fecha / id", "Descripción", "Resumen")
        self.controller.load()
        self._sync_widgets()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id != "search":
            return
        self.controller.apply_query(event.value)
        self._sync_widgets()

    def action_cursor_down(self) -> None:
        self.controller.move_selection(1)
        self._sync_widgets()

    def action_cursor_up(self) -> None:
        self.controller.move_selection(-1)
        self._sync_widgets()

    def action_reload(self) -> None:
        self.controller.load(
            query=self.controller.state.query,
            selected_id=self.controller.state.selected_id,
        )
        self._sync_widgets()

    async def action_open_selected(self) -> None:
        row = selected_row(self.controller.state)
        if row is None:
            self.controller.status_message = "No hay una sesión visible para abrir."
            self._sync_widgets()
            return

        try:
            with self.suspend():
                self.controller.open_selected()
        except SuspendNotSupported:
            self.controller.open_selected()
        self._sync_widgets()

    def _sync_widgets(self) -> None:
        self.query_one("#status", Static).update(self._status_text())
        table = self.query_one("#sessions", DataTable)
        table.clear(columns=False)
        for row in self.controller.state.visible_sessions:
            table.add_row(row.title, row.context, row.description, row.summary, key=row.id)

        index = selected_index_or_none(self.controller.state)
        if index is not None:
            table.move_cursor(row=index)

    def _status_text(self) -> str:
        if self.controller.error_message:
            return f"{self.controller.error_message}\n{self.controller.status_message}"
        return self.controller.status_message


def selected_row(state: SessionListState) -> SessionRow | None:
    if state.selected_id is None:
        return None
    return next((row for row in state.visible_sessions if row.id == state.selected_id), None)


def selected_index(state: SessionListState) -> int:
    return selected_index_or_none(state) or 0


def selected_index_or_none(state: SessionListState) -> int | None:
    if state.selected_id is None:
        return None
    for index, row in enumerate(state.visible_sessions):
        if row.id == state.selected_id:
            return index
    return None


def describe_state(cwd: Path, state: SessionListState) -> str:
    total = len(state.all_sessions)
    visible = len(state.visible_sessions)
    if total == 0:
        return (
            f"No hay sesiones para {cwd}. Abrí una sesión de OpenCode en este directorio "
            "y volvé a intentar."
        )
    if visible == 0:
        return f"Sin resultados para el filtro actual en {cwd}. Borrá o ajustá la búsqueda."
    if state.query:
        return (
            f"{visible} de {total} sesiones visibles para el filtro actual. "
            "Enter abre la selección."
        )
    return f"{total} sesiones para {cwd}. Escribí para buscar; Enter abre la selección."
