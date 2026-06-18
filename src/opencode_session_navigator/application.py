from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Literal, Protocol

from opencode_session_navigator.domain import SessionRow, matches_query
from opencode_session_navigator.infra.sqlite_repo import SessionRecord
from opencode_session_navigator.text import derive_description, derive_summary, normalize_text

DEFAULT_DESCRIPTION_LIMIT = 120
DEFAULT_SUMMARY_LIMIT = 160


class SessionViewMode(StrEnum):
    ROOTS = "roots"
    ALL = "all"


class SessionRepository(Protocol):
    def list_sessions(self, cwd: Path) -> list[SessionRecord]: ...


@dataclass(frozen=True)
class SessionListState:
    all_sessions: tuple[SessionRow, ...]
    visible_sessions: tuple[SessionRow, ...]
    query: str
    selected_id: str | None
    view_mode: SessionViewMode = SessionViewMode.ROOTS

    @classmethod
    def from_sessions(
        cls,
        sessions: tuple[SessionRow, ...] | list[SessionRow],
        *,
        query: str = "",
        selected_id: str | None = None,
        view_mode: SessionViewMode = SessionViewMode.ROOTS,
    ) -> SessionListState:
        rows = tuple(sessions)
        return cls(
            all_sessions=rows,
            visible_sessions=(),
            query="",
            selected_id=selected_id,
            view_mode=view_mode,
        ).with_query(query)

    def with_query(self, query: str) -> SessionListState:
        normalized_query = normalize_text(query)
        visible = visible_rows(self.all_sessions, normalized_query, self.view_mode)
        selected_id = preserve_selection(visible, self.selected_id)
        return SessionListState(
            all_sessions=self.all_sessions,
            visible_sessions=visible,
            query=normalized_query,
            selected_id=selected_id,
            view_mode=self.view_mode,
        )

    def with_view_mode(self, view_mode: SessionViewMode) -> SessionListState:
        visible = visible_rows(self.all_sessions, self.query, view_mode)
        selected_id = preserve_selection(visible, self.selected_id)
        return SessionListState(
            all_sessions=self.all_sessions,
            visible_sessions=visible,
            query=self.query,
            selected_id=selected_id,
            view_mode=view_mode,
        )

    def with_selected_id(self, selected_id: str | None) -> SessionListState:
        if selected_id is None:
            next_selected = None
        else:
            visible_ids = {row.id for row in self.visible_sessions}
            next_selected = selected_id if selected_id in visible_ids else self.selected_id
        return SessionListState(
            all_sessions=self.all_sessions,
            visible_sessions=self.visible_sessions,
            query=self.query,
            selected_id=next_selected,
            view_mode=self.view_mode,
        )


@dataclass(frozen=True)
class SessionNavigator:
    repository: SessionRepository
    description_limit: int = DEFAULT_DESCRIPTION_LIMIT
    summary_limit: int = DEFAULT_SUMMARY_LIMIT

    def load(
        self,
        cwd: Path,
        *,
        query: str = "",
        selected_id: str | None = None,
        view_mode: SessionViewMode = SessionViewMode.ROOTS,
    ) -> SessionListState:
        records = self.repository.list_sessions(cwd)
        rows = tuple(
            record_to_row(record, self.description_limit, self.summary_limit) for record in records
        )
        return SessionListState.from_sessions(
            rows, query=query, selected_id=selected_id, view_mode=view_mode
        )


def record_to_row(record: SessionRecord, description_limit: int, summary_limit: int) -> SessionRow:
    description = derive_description(record.user_texts, description_limit)
    summary = derive_summary(record.assistant_texts, record.user_texts, summary_limit)
    return SessionRow.create(
        session_id=record.id,
        parent_id=record.parent_id,
        title=record.title,
        description=description,
        summary=summary,
        updated_at=record.time_updated,
    )


def visible_rows(
    rows: tuple[SessionRow, ...], query: str, view_mode: SessionViewMode
) -> tuple[SessionRow, ...]:
    if view_mode == SessionViewMode.ALL:
        ordered = grouped_rows(rows)
        return contextual_root_rows(ordered, query) if query else ordered
    if not query:
        return tuple(
            row.with_visual_metadata(depth=0, kind="root") for row in rows if row.parent_id is None
        )
    return contextual_root_rows(rows, query)


def grouped_rows(rows: tuple[SessionRow, ...]) -> tuple[SessionRow, ...]:
    by_parent: dict[str | None, list[SessionRow]] = {}
    by_id = {row.id: row for row in rows}
    for row in rows:
        by_parent.setdefault(row.parent_id, []).append(row)

    ordered: list[SessionRow] = []
    visited: set[str] = set()

    def append_branch(row: SessionRow, depth: int) -> None:
        visited.add(row.id)
        kind: Literal["root", "child"] = "root" if depth == 0 else "child"
        ordered.append(row.with_visual_metadata(depth=depth, kind=kind))
        for child in by_parent.get(row.id, []):
            append_branch(child, depth + 1)

    for root in by_parent.get(None, []):
        append_branch(root, 0)

    for row in rows:
        if row.id not in visited and row.parent_id not in by_id:
            visited.add(row.id)
            ordered.append(row.with_visual_metadata(depth=0, kind="orphan"))
    for row in rows:
        if row.id not in visited:
            visited.add(row.id)
            ordered.append(row.with_visual_metadata(depth=1, kind="child"))
    return tuple(ordered)


def contextual_root_rows(rows: tuple[SessionRow, ...], query: str) -> tuple[SessionRow, ...]:
    by_id = {row.id: row for row in rows}
    visible: list[SessionRow] = []
    added: set[str] = set()
    for row in rows:
        if not matches_query(row, query):
            continue
        if row.parent_id is None:
            if row.id not in added:
                visible.append(row.with_visual_metadata(depth=0, kind="root"))
                added.add(row.id)
            continue

        root = available_root(row, by_id)
        if root is not None and root.id not in added:
            visible.append(root.with_visual_metadata(depth=0, kind="root"))
            added.add(root.id)
        if row.id not in added:
            kind: Literal["child", "orphan"] = "child" if root is not None else "orphan"
            depth = 1 if root is not None else 0
            visible.append(row.with_visual_metadata(depth=depth, kind=kind))
            added.add(row.id)
    return tuple(visible)


def available_root(row: SessionRow, by_id: dict[str, SessionRow]) -> SessionRow | None:
    seen = {row.id}
    current = row
    while current.parent_id is not None:
        parent = by_id.get(current.parent_id)
        if parent is None or parent.id in seen:
            return None
        if parent.parent_id is None:
            return parent
        seen.add(parent.id)
        current = parent
    return current


def preserve_selection(
    visible_sessions: tuple[SessionRow, ...], selected_id: str | None
) -> str | None:
    if not visible_sessions:
        return None
    if selected_id and any(row.id == selected_id for row in visible_sessions):
        return selected_id
    return visible_sessions[0].id
