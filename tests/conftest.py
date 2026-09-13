from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from pathlib import Path

import pytest


@pytest.fixture
def codex_database(tmp_path: Path):
    def create(rows: Iterable[tuple[object, ...]]) -> Path:
        database = tmp_path / "state_5.sqlite"
        connection = sqlite3.connect(database)
        connection.executescript(
            """
            CREATE TABLE threads (
                id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                title TEXT NOT NULL,
                name TEXT,
                first_user_message TEXT NOT NULL DEFAULT '',
                cwd TEXT NOT NULL,
                updated_at INTEGER NOT NULL,
                updated_at_ms INTEGER,
                thread_source TEXT,
                preview TEXT NOT NULL DEFAULT ''
            );
            """
        )
        connection.executemany(
            """
            INSERT INTO threads (
                id, source, title, name, first_user_message, cwd,
                updated_at, updated_at_ms, thread_source, preview
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        connection.commit()
        connection.close()
        return database

    return create
