from __future__ import annotations

import os
import re
import sqlite3
from pathlib import Path

from agent_sessions.inventory import (
    Session,
    SessionSourceError,
    clean_text,
    timestamp_from_milliseconds,
)

_STATE_DATABASE = re.compile(r"state_(\d+)\.sqlite$")


class CodexSessionProvider:
    def __init__(self, database: Path | None = None) -> None:
        self._database = database

    def list_sessions(self, *, limit: int) -> list[Session]:
        database = self._database or find_codex_database()
        try:
            connection = sqlite3.connect(
                f"{database.resolve().as_uri()}?mode=ro", uri=True
            )
        except sqlite3.Error as exc:
            raise SessionSourceError(
                f"cannot open Codex session database: {database}"
            ) from exc

        connection.row_factory = sqlite3.Row
        try:
            columns = _thread_columns(connection)
            query = _session_query(columns)
            rows = connection.execute(query, (limit,)).fetchall()
            sessions = [_session_from_row(row) for row in rows]
        except SessionSourceError:
            raise
        except (sqlite3.Error, TypeError, ValueError) as exc:
            raise SessionSourceError(
                f"cannot read Codex sessions from: {database}"
            ) from exc
        finally:
            connection.close()

        return sessions


def find_codex_database(codex_home: Path | None = None) -> Path:
    root = codex_home
    if root is None:
        configured = os.environ.get("CODEX_HOME")
        root = Path(configured).expanduser() if configured else Path.home() / ".codex"

    candidates: list[tuple[int, Path]] = []
    for path in root.glob("state_*.sqlite"):
        match = _STATE_DATABASE.fullmatch(path.name)
        if match and path.is_file():
            candidates.append((int(match.group(1)), path))

    if not candidates:
        raise SessionSourceError(f"no Codex state database found under: {root}")
    return max(candidates, key=lambda candidate: candidate[0])[1]


def _thread_columns(connection: sqlite3.Connection) -> set[str]:
    columns = {str(row[1]) for row in connection.execute("PRAGMA table_info(threads)")}
    required = {"id", "source", "title", "cwd", "updated_at"}
    missing = required - columns
    if missing:
        names = ", ".join(sorted(missing))
        raise SessionSourceError(
            f"Codex threads table is missing required columns: {names}"
        )
    return columns


def _session_query(columns: set[str]) -> str:
    name = "NULLIF(TRIM(name), '')" if "name" in columns else "NULL"
    first_prompt = (
        "NULLIF(TRIM(first_user_message), '')"
        if "first_user_message" in columns
        else "NULL"
    )
    updated = (
        "COALESCE(NULLIF(updated_at_ms, 0), updated_at * 1000)"
        if "updated_at_ms" in columns
        else "updated_at * 1000"
    )
    root_session = (
        "AND COALESCE(thread_source, '') <> 'subagent'"
        if "thread_source" in columns
        else ""
    )
    visible_session = "AND preview <> ''" if "preview" in columns else ""
    return f"""
        SELECT
            id,
            COALESCE({name}, NULLIF(TRIM(title), ''), {first_prompt}, id) AS session_title,
            {first_prompt} AS first_prompt,
            NULLIF(TRIM(cwd), '') AS cwd,
            {updated} AS updated_ms
        FROM threads
        WHERE source IN ('cli', 'vscode')
        {root_session}
        {visible_session}
        ORDER BY updated_ms DESC, id DESC
        LIMIT ?
    """


def _session_from_row(row: sqlite3.Row) -> Session:
    session_id = str(row["id"])
    return Session(
        provider="codex",
        session_id=session_id,
        session_title=clean_text(row["session_title"]) or session_id,
        session_first_prompt=clean_text(row["first_prompt"]),
        cwd=clean_text(row["cwd"]),
        updated_at=timestamp_from_milliseconds(int(row["updated_ms"])),
    )
