from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from opencode_session_navigator.infra.sqlite_repo import (
    IncompatibleSchemaError,
    SQLiteRepositoryError,
    SQLiteSessionRepository,
)


def test_list_sessions_filtra_por_cwd_exacto(tmp_path: Path) -> None:
    db_path = crear_db_valida(tmp_path)
    cwd = tmp_path / "repo" / "app"
    insertar_sesion(db_path, "ses_app", str(cwd), "App", 20)
    insertar_sesion(db_path, "ses_parent", str(tmp_path / "repo"), "Padre", 30)
    insertar_sesion(db_path, "ses_child", str(cwd / "sub"), "Hija", 40)
    insertar_texto(db_path, "ses_app", "msg_1", "part_1", "user", "hola desde app")
    insertar_texto(db_path, "ses_app", "msg_2", "part_2", "assistant", "respuesta útil")

    records = SQLiteSessionRepository(db_path).list_sessions(cwd)

    assert [record.id for record in records] == ["ses_app"]
    assert records[0].user_texts == ("hola desde app",)
    assert records[0].assistant_texts == ("respuesta útil",)


def test_list_sessions_devuelve_lista_vacia_para_cwd_sin_sesiones(tmp_path: Path) -> None:
    db_path = crear_db_valida(tmp_path)

    assert SQLiteSessionRepository(db_path).list_sessions(tmp_path / "sin-sesiones") == []


def test_list_sessions_rechaza_esquema_incompatible(tmp_path: Path) -> None:
    db_path = tmp_path / "opencode.db"
    with sqlite3.connect(db_path) as connection:
        connection.execute("CREATE TABLE session (id TEXT PRIMARY KEY)")

    with pytest.raises(IncompatibleSchemaError, match="Faltan columnas"):
        SQLiteSessionRepository(db_path).list_sessions(tmp_path)


def test_list_sessions_rechaza_message_sin_time_created(tmp_path: Path) -> None:
    db_path = tmp_path / "opencode.db"
    with sqlite3.connect(db_path) as connection:
        connection.executescript(
            """
            CREATE TABLE session (
                id TEXT PRIMARY KEY,
                directory TEXT NOT NULL,
                title TEXT,
                time_created INTEGER,
                time_updated INTEGER
            );
            CREATE TABLE message (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                data TEXT NOT NULL
            );
            CREATE TABLE part (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                message_id TEXT NOT NULL,
                data TEXT NOT NULL
            );
            """
        )

    with pytest.raises(IncompatibleSchemaError, match="Faltan columnas en message: time_created"):
        SQLiteSessionRepository(db_path).list_sessions(tmp_path)


def test_list_sessions_ignora_json_y_partes_desconocidas(tmp_path: Path) -> None:
    db_path = crear_db_valida(tmp_path)
    cwd = tmp_path / "repo"
    insertar_sesion(db_path, "ses_1", str(cwd), "Título", 10)
    insertar_parte_cruda(db_path, "ses_1", "msg_bad", "part_bad", "no-json", "no-json")
    insertar_parte_cruda(
        db_path,
        "ses_1",
        "msg_tool",
        "part_tool",
        json.dumps({"role": "assistant"}),
        json.dumps({"type": "tool", "text": "ignorado"}),
    )
    insertar_texto(db_path, "ses_1", "msg_ok", "part_ok", "assistant", "texto válido")

    records = SQLiteSessionRepository(db_path).list_sessions(cwd)

    assert records[0].assistant_texts == ("texto válido",)


def test_list_sessions_elimina_secuencias_de_control_en_mensajes(tmp_path: Path) -> None:
    db_path = crear_db_valida(tmp_path)
    cwd = tmp_path / "repo"
    insertar_sesion(db_path, "ses_1", str(cwd), "Título", 10)
    insertar_texto(db_path, "ses_1", "msg_1", "part_1", "user", "\x1b[31mprompt\x1b[0m\x07 útil")

    records = SQLiteSessionRepository(db_path).list_sessions(cwd)

    assert records[0].user_texts == ("prompt útil",)


def test_repositorio_abre_base_en_solo_lectura(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db_path = crear_db_valida(tmp_path)
    llamadas: list[tuple[str, bool]] = []
    conectar_original = sqlite3.connect

    def conectar_espiado(database: str, *, uri: bool = False) -> sqlite3.Connection:
        llamadas.append((database, uri))
        return conectar_original(database, uri=uri)

    monkeypatch.setattr("sqlite3.connect", conectar_espiado)

    SQLiteSessionRepository(db_path).list_sessions(tmp_path)

    assert llamadas == [(f"file:{db_path}?mode=ro", True)]


def test_repositorio_reporta_db_ausente(tmp_path: Path) -> None:
    with pytest.raises(SQLiteRepositoryError, match="No existe"):
        SQLiteSessionRepository(tmp_path / "ausente.db").list_sessions(tmp_path)


def test_repositorio_envuelve_db_corrupta(tmp_path: Path) -> None:
    db_path = tmp_path / "opencode.db"
    db_path.write_text("no es sqlite", encoding="utf-8")

    with pytest.raises(SQLiteRepositoryError, match="No se pudo consultar"):
        SQLiteSessionRepository(db_path).list_sessions(tmp_path)


def test_repositorio_envuelve_fallo_de_apertura(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db_path = crear_db_valida(tmp_path)

    def fallar_conexion(database: str, *, uri: bool = False) -> sqlite3.Connection:
        raise sqlite3.DatabaseError("permiso denegado")

    monkeypatch.setattr("sqlite3.connect", fallar_conexion)

    with pytest.raises(SQLiteRepositoryError, match="No se pudo abrir"):
        SQLiteSessionRepository(db_path).list_sessions(tmp_path)


def test_repositorio_envuelve_fallo_durante_validacion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db_path = crear_db_valida(tmp_path)

    def fallar_validacion(self: SQLiteSessionRepository, connection: sqlite3.Connection) -> None:
        raise sqlite3.DatabaseError("pragma falló")

    monkeypatch.setattr(SQLiteSessionRepository, "_validate_schema", fallar_validacion)

    with pytest.raises(SQLiteRepositoryError, match="No se pudo consultar"):
        SQLiteSessionRepository(db_path).list_sessions(tmp_path)


def crear_db_valida(tmp_path: Path) -> Path:
    db_path = tmp_path / "opencode.db"
    with sqlite3.connect(db_path) as connection:
        connection.executescript(
            """
            CREATE TABLE session (
                id TEXT PRIMARY KEY,
                directory TEXT NOT NULL,
                title TEXT,
                time_created INTEGER,
                time_updated INTEGER
            );
            CREATE TABLE message (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                data TEXT NOT NULL,
                time_created INTEGER
            );
            CREATE TABLE part (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                message_id TEXT NOT NULL,
                data TEXT NOT NULL
            );
            """
        )
    return db_path


def insertar_sesion(
    db_path: Path, session_id: str, directory: str, title: str, updated: int
) -> None:
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO session (id, directory, title, time_created, time_updated)
            VALUES (?, ?, ?, ?, ?)
            """,
            (session_id, directory, title, updated - 1, updated),
        )


def insertar_texto(
    db_path: Path, session_id: str, message_id: str, part_id: str, role: str, text: str
) -> None:
    insertar_parte_cruda(
        db_path,
        session_id,
        message_id,
        part_id,
        json.dumps({"role": role}),
        json.dumps({"type": "text", "text": text}),
    )


def insertar_parte_cruda(
    db_path: Path,
    session_id: str,
    message_id: str,
    part_id: str,
    message_data: str,
    part_data: str,
) -> None:
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            "INSERT INTO message (id, session_id, data, time_created) VALUES (?, ?, ?, 1)",
            (message_id, session_id, message_data),
        )
        connection.execute(
            "INSERT INTO part (id, session_id, message_id, data) VALUES (?, ?, ?, ?)",
            (part_id, session_id, message_id, part_data),
        )
