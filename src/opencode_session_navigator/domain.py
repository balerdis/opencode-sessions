from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from opencode_session_navigator.text import normalize_search_text, normalize_text

TITLE_PLACEHOLDER = "Sin título"


@dataclass(frozen=True)
class SessionText:
    description: str
    summary: str


@dataclass(frozen=True)
class SessionRow:
    id: str
    title: str
    context: str
    description: str
    summary: str
    searchable_text: str
    updated_at: int | None

    @classmethod
    def create(
        cls,
        *,
        session_id: str,
        title: str | None,
        description: str,
        summary: str,
        updated_at: int | None,
    ) -> SessionRow:
        normalized_title = normalize_text(title) or TITLE_PLACEHOLDER
        normalized_description = normalize_text(description)
        normalized_summary = normalize_text(summary)
        context = format_context(session_id=session_id, updated_at=updated_at)
        searchable_text = normalize_search_text(
            " ".join((normalized_title, normalized_description, normalized_summary))
        )
        return cls(
            id=session_id,
            title=normalized_title,
            context=context,
            description=normalized_description,
            summary=normalized_summary,
            searchable_text=searchable_text,
            updated_at=updated_at,
        )


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
