from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

from opencode_session_navigator.text import normalize_search_text, normalize_text

TITLE_PLACEHOLDER = "Sin título"


@dataclass(frozen=True)
class SessionText:
    description: str
    summary: str


@dataclass(frozen=True)
class SessionRow:
    id: str
    parent_id: str | None
    title: str
    display_title: str
    context: str
    description: str
    summary: str
    searchable_text: str
    updated_at: int | None
    depth: int = 0
    kind: Literal["root", "child", "orphan"] = "root"

    @classmethod
    def create(
        cls,
        *,
        session_id: str,
        title: str | None,
        description: str,
        summary: str,
        updated_at: int | None,
        parent_id: str | None = None,
        depth: int = 0,
        kind: Literal["root", "child", "orphan"] | None = None,
    ) -> SessionRow:
        normalized_title = normalize_text(title) or TITLE_PLACEHOLDER
        normalized_description = normalize_text(description)
        normalized_summary = normalize_text(summary)
        context = format_context(session_id=session_id, updated_at=updated_at)
        searchable_text = normalize_search_text(
            " ".join((normalized_title, normalized_description, normalized_summary))
        )
        row_kind: Literal["root", "child", "orphan"] = kind or (
            "root" if parent_id is None else "child"
        )
        return cls(
            id=session_id,
            parent_id=parent_id,
            title=normalized_title,
            display_title=format_display_title(normalized_title, depth=depth, kind=row_kind),
            context=context,
            description=normalized_description,
            summary=normalized_summary,
            searchable_text=searchable_text,
            updated_at=updated_at,
            depth=depth,
            kind=row_kind,
        )

    def with_visual_metadata(
        self, *, depth: int, kind: Literal["root", "child", "orphan"]
    ) -> SessionRow:
        return SessionRow(
            id=self.id,
            parent_id=self.parent_id,
            title=self.title,
            display_title=format_display_title(self.title, depth=depth, kind=kind),
            context=self.context,
            description=self.description,
            summary=self.summary,
            searchable_text=self.searchable_text,
            updated_at=self.updated_at,
            depth=depth,
            kind=kind,
        )


def format_display_title(
    title: str, *, depth: int, kind: Literal["root", "child", "orphan"]
) -> str:
    if kind == "orphan":
        return f"↳ Huérfana · {title}"
    if depth <= 0:
        return title
    return f"{'  ' * (depth - 1)}└─ {title}"


def matches_query(row: SessionRow, query: str) -> bool:
    normalized_query = normalize_search_text(query)
    if not normalized_query:
        return True
    return normalized_query in row.searchable_text


def format_context(*, session_id: str, updated_at: int | None) -> str:
    short_id = session_id[:8] if len(session_id) > 8 else session_id
    if updated_at is None:
        return f"id {short_id}"

    timestamp = updated_at / 1000 if updated_at > 10_000_000_000 else updated_at
    try:
        formatted = datetime.fromtimestamp(timestamp, tz=UTC).strftime("%Y-%m-%d %H:%M")
    except (OverflowError, OSError, ValueError):
        return f"id {short_id}"
    return f"{formatted} · id {short_id}"
