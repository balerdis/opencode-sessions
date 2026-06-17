from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote

from opencode_session_navigator.text import normalize_text


class SQLiteRepositoryError(RuntimeError):
    """Error base del repositorio SQLite."""


class IncompatibleSchemaError(SQLiteRepositoryError):
    """El esquema de SQLite no contiene las tablas o columnas esperadas."""


@dataclass(frozen=True)
class SessionRecord:
    id: str
    title: str | None
    directory: str
    time_created: int | None
    time_updated: int | None
    user_texts: tuple[str, ...]
    assistant_texts: tuple[str, ...]


class SQLiteSessionRepository:
    required_columns = {
        "session": {"id", "directory", "title", "time_created", "time_updated"},
        "message": {"id", "session_id", "data", "time_created"},
        "part": {"id", "session_id", "message_id", "data"},
    }

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def list_sessions(self, cwd: Path) -> list[SessionRecord]:
        resolved_cwd = str(cwd.resolve())
        try:
            with self._connect_read_only() as connection:
                self._validate_schema(connection)
                rows = connection.execute(
                    """
                    SELECT id, title, directory, time_created, time_updated
                    FROM session
                    WHERE directory = ?
                    ORDER BY time_updated DESC, time_created DESC, id ASC
                    """,
                    (resolved_cwd,),
                ).fetchall()

                records: list[SessionRecord] = []
                for row in rows:
                    user_texts, assistant_texts = self._load_texts(connection, row["id"])
                    records.append(
                        SessionRecord(
                            id=row["id"],
                            title=row["title"],
                            directory=row["directory"],
                            time_created=row["time_created"],
                            time_updated=row["time_updated"],
                            user_texts=tuple(user_texts),
                            assistant_texts=tuple(assistant_texts),
                        )
                    )
                return records
        except SQLiteRepositoryError:
            raise
        except sqlite3.DatabaseError as error:
            message = f"No se pudo consultar la base de OpenCode: {error}"
            raise SQLiteRepositoryError(message) from error

    def _connect_read_only(self) -> sqlite3.Connection:
        if not self.db_path.exists():
            raise SQLiteRepositoryError(f"No existe la base de OpenCode: {self.db_path}")

        uri = f"file:{quote(str(self.db_path))}?mode=ro"
        try:
            connection = sqlite3.connect(uri, uri=True)
        except sqlite3.Error as error:
            message = f"No se pudo abrir la base en solo lectura: {error}"
            raise SQLiteRepositoryError(message) from error

        connection.row_factory = sqlite3.Row
        return connection

    def _validate_schema(self, connection: sqlite3.Connection) -> None:
        existing_tables = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }

        for table, required in self.required_columns.items():
            if table not in existing_tables:
                raise IncompatibleSchemaError(f"Falta la tabla requerida: {table}")

            columns = {row["name"] for row in connection.execute(f"PRAGMA table_info({table})")}
            missing = sorted(required - columns)
            if missing:
                missing_list = ", ".join(missing)
                raise IncompatibleSchemaError(f"Faltan columnas en {table}: {missing_list}")

    def _load_texts(
        self, connection: sqlite3.Connection, session_id: str
    ) -> tuple[list[str], list[str]]:
        user_texts: list[str] = []
        assistant_texts: list[str] = []
        rows = connection.execute(
            """
            SELECT message.data AS message_data, part.data AS part_data
            FROM message
            JOIN part ON part.message_id = message.id
            WHERE message.session_id = ?
            ORDER BY message.time_created ASC, part.id ASC
            """,
            (session_id,),
        ).fetchall()

        for row in rows:
            role = _json_value(row["message_data"], "role")
            text = _text_part(row["part_data"])
            if not text:
                continue
            if role == "user":
                user_texts.append(text)
            elif role == "assistant":
                assistant_texts.append(text)

        return user_texts, assistant_texts


def _json_value(raw_json: str, key: str) -> Any | None:
    try:
        payload = json.loads(raw_json)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return payload.get(key)


def _text_part(raw_json: str) -> str | None:
    try:
        payload = json.loads(raw_json)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict) or payload.get("type") != "text":
        return None
    text = payload.get("text")
    if not isinstance(text, str):
        return None
    normalized = normalize_text(text)
    return normalized or None
