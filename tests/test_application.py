from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from opencode_session_navigator.application import SessionListState, SessionNavigator
from opencode_session_navigator.domain import SessionRow
from opencode_session_navigator.infra.sqlite_repo import SessionRecord


def test_load_construye_filas_con_placeholders_y_contexto() -> None:
    repository = FakeRepository(
        [
            SessionRecord(
                id="session-123456",
                title="  ",
                directory="/repo",
                time_created=1,
                time_updated=1_700_000_000,
                user_texts=("",),
                assistant_texts=(),
            )
        ]
    )

    state = SessionNavigator(repository).load(Path("/repo"))

    row = state.visible_sessions[0]
    assert row.title == "Sin título"
    assert row.description == "Sin descripción disponible."
    assert row.summary == "Sin resumen disponible."
    assert row.context.endswith("id session-")
    assert state.selected_id == "session-123456"


def test_load_recorta_descripcion_al_limite_configurado() -> None:
    repository = FakeRepository(
        [
            SessionRecord(
                id="session-1",
                title="Título",
                directory="/repo",
                time_created=1,
                time_updated=1,
                user_texts=("descripción demasiado larga para la fila",),
                assistant_texts=(),
            )
        ]
    )

    state = SessionNavigator(repository, description_limit=12).load(Path("/repo"))

    assert state.visible_sessions[0].description == "descripci..."
    assert len(state.visible_sessions[0].description) == 12


def test_load_formatea_contexto_con_timestamp_visible_y_fila_completa() -> None:
    repository = FakeRepository(
        [
            SessionRecord(
                id="session-abcdef123456",
                title="Investigación SQLite",
                directory="/repo",
                time_created=1_700_000_000,
                time_updated=1_700_000_000_000,
                user_texts=("buscar sesiones por cwd",),
                assistant_texts=("usar message y part",),
            )
        ]
    )

    state = SessionNavigator(repository).load(Path("/repo"))

    row = state.visible_sessions[0]
    assert row.id == "session-abcdef123456"
    assert row.title == "Investigación SQLite"
    assert row.context == "2023-11-14 22:13 · id session-"
    assert row.description == "buscar sesiones por cwd"
    assert row.summary == "usar message y part"
    assert "investigación sqlite" in row.searchable_text
    assert "buscar sesiones por cwd" in row.searchable_text
    assert "usar message y part" in row.searchable_text


def test_load_elimina_secuencias_de_control_de_textos_visibles() -> None:
    repository = FakeRepository(
        [
            SessionRecord(
                id="session-1",
                title="\x1b[32mTítulo\x1b[0m",
                directory="/repo",
                time_created=1,
                time_updated=1,
                user_texts=("prompt\x07 visible",),
                assistant_texts=("\x1b]0;oculto\x07resumen",),
            )
        ]
    )

    row = SessionNavigator(repository).load(Path("/repo")).visible_sessions[0]

    assert row.title == "Título"
    assert row.description == "prompt visible"
    assert row.summary == "resumen"


def test_busqueda_en_memoria_incluye_descripcion_y_resumen() -> None:
    rows = (
        make_row("a", title="Título", description="prompt con docker", summary="respuesta"),
        make_row("b", title="Otro", description="sin match", summary="menciona pytest"),
    )

    state = SessionListState.from_sessions(rows).with_query("pytest")

    assert [row.id for row in state.visible_sessions] == ["b"]
    assert state.selected_id == "b"


def test_busqueda_vacia_devuelve_todas_las_sesiones() -> None:
    rows = (make_row("a"), make_row("b"))

    state = SessionListState.from_sessions(rows).with_query("   ")

    assert [row.id for row in state.visible_sessions] == ["a", "b"]
    assert state.selected_id == "a"


def test_preserva_seleccion_si_sigue_visible_tras_filtrar() -> None:
    rows = (
        make_row("a", description="python"),
        make_row("b", description="python sqlite"),
    )
    state = SessionListState.from_sessions(rows, selected_id="b")

    filtered = state.with_query("python")

    assert [row.id for row in filtered.visible_sessions] == ["a", "b"]
    assert filtered.selected_id == "b"


def test_selecciona_primer_resultado_si_la_seleccion_sale_del_filtro() -> None:
    rows = (
        make_row("a", description="python"),
        make_row("b", description="sqlite"),
    )
    state = SessionListState.from_sessions(rows, selected_id="b")

    filtered = state.with_query("python")

    assert [row.id for row in filtered.visible_sessions] == ["a"]
    assert filtered.selected_id == "a"


def test_sin_resultados_no_deja_seleccion_colgante() -> None:
    state = SessionListState.from_sessions((make_row("a"),), selected_id="a")

    filtered = state.with_query("no existe")

    assert filtered.visible_sessions == ()
    assert filtered.selected_id is None


@dataclass(frozen=True)
class FakeRepository:
    records: list[SessionRecord]

    def list_sessions(self, cwd: Path) -> list[SessionRecord]:
        return self.records


def make_row(
    session_id: str,
    *,
    title: str = "Título",
    description: str = "Descripción",
    summary: str = "Resumen",
) -> SessionRow:
    return SessionRow.create(
        session_id=session_id,
        title=title,
        description=description,
        summary=summary,
        updated_at=None,
    )
