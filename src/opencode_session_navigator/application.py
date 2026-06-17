from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from opencode_session_navigator.domain import SessionRow, matches_query
from opencode_session_navigator.infra.sqlite_repo import SessionRecord
from opencode_session_navigator.text import derive_description, derive_summary, normalize_text

DEFAULT_DESCRIPTION_LIMIT = 120
DEFAULT_SUMMARY_LIMIT = 160


class SessionRepository(Protocol):
    def list_sessions(self, cwd: Path) -> list[SessionRecord]: ...


@dataclass(frozen=True)
class SessionListState:
    all_sessions: tuple[SessionRow, ...]
    visible_sessions: tuple[SessionRow, ...]
    query: str
    selected_id: str | None

    @classmethod
    def from_sessions(
        cls,
        sessions: tuple[SessionRow, ...] | list[SessionRow],
        *,
        query: str = "",
        selected_id: str | None = None,
    ) -> SessionListState:
        rows = tuple(sessions)
        return cls(
            all_sessions=rows,
            visible_sessions=(),
            query="",
            selected_id=selected_id,
        ).with_query(query)

    def with_query(self, query: str) -> SessionListState:
        normalized_query = normalize_text(query)
        visible = tuple(row for row in self.all_sessions if matches_query(row, normalized_query))
        selected_id = preserve_selection(visible, self.selected_id)
        return SessionListState(
            all_sessions=self.all_sessions,
            visible_sessions=visible,
            query=normalized_query,
            selected_id=selected_id,
        )

    def with_selected_id(self, selected_id: str | None) -> SessionListState:
        visible_ids = {row.id for row in self.visible_sessions}
        next_selected = selected_id if selected_id in visible_ids else self.selected_id
        return SessionListState(
            all_sessions=self.all_sessions,
            visible_sessions=self.visible_sessions,
            query=self.query,
            selected_id=next_selected,
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
    ) -> SessionListState:
        records = self.repository.list_sessions(cwd)
        rows = tuple(
            record_to_row(record, self.description_limit, self.summary_limit) for record in records
        )
        return SessionListState.from_sessions(rows, query=query, selected_id=selected_id)


def record_to_row(record: SessionRecord, description_limit: int, summary_limit: int) -> SessionRow:
    description = derive_description(record.user_texts, description_limit)
    summary = derive_summary(record.assistant_texts, record.user_texts, summary_limit)
    return SessionRow.create(
        session_id=record.id,
        title=record.title,
        description=description,
        summary=summary,
        updated_at=record.time_updated,
    )


def preserve_selection(
    visible_sessions: tuple[SessionRow, ...], selected_id: str | None
) -> str | None:
    if not visible_sessions:
        return None
    if selected_id and any(row.id == selected_id for row in visible_sessions):
        return selected_id
    return visible_sessions[0].id
