from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from agent_sessions.inventory import SessionSourceError
from agent_sessions.providers.codex import CodexSessionProvider, find_codex_database


def test_codex_maps_root_sessions_and_excludes_internal_records(codex_database) -> None:
    database = codex_database(
        [
            (
                "root",
                "vscode",
                "Fallback title",
                "Custom title",
                "First prompt",
                "/one",
                1,
                3000,
                "user",
                "Visible",
            ),
            ("cli", "cli", "CLI title", None, "", "/two", 2, None, None, "Visible"),
            ("empty", "cli", "", None, "", "/two", 5, 6000, "user", ""),
            (
                "subagent",
                "vscode",
                "Worker",
                None,
                "Do work",
                "/one",
                3,
                4000,
                "subagent",
                "Visible",
            ),
            ("exec", "exec", "Exec", None, "Run", "/one", 4, 5000, "user", "Visible"),
        ]
    )

    result = CodexSessionProvider(database).list_sessions(limit=100)

    assert [item.session_id for item in result] == ["root", "cli"]
    assert result[0].session_title == "Custom title"
    assert result[0].session_first_prompt == "First prompt"
    assert result[1].session_title == "CLI title"
    assert result[1].session_first_prompt is None
    assert result[1].updated_at.timestamp() == 2


def test_codex_supports_the_older_required_schema(tmp_path: Path) -> None:
    database = tmp_path / "state_4.sqlite"
    connection = sqlite3.connect(database)
    connection.executescript(
        """
        CREATE TABLE threads (
            id TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            title TEXT NOT NULL,
            cwd TEXT NOT NULL,
            updated_at INTEGER NOT NULL
        );
        INSERT INTO threads VALUES ('older', 'cli', 'Old schema', '/old', 7);
        """
    )
    connection.close()

    result = CodexSessionProvider(database).list_sessions(limit=1)

    assert result[0].session_id == "older"
    assert result[0].session_first_prompt is None
    assert result[0].updated_at.timestamp() == 7


def test_find_codex_database_chooses_highest_number(tmp_path: Path) -> None:
    (tmp_path / "state_4.sqlite").touch()
    expected = tmp_path / "state_12.sqlite"
    expected.touch()
    (tmp_path / "state_backup.sqlite").touch()

    assert find_codex_database(tmp_path) == expected


def test_find_codex_database_reports_missing_store(tmp_path: Path) -> None:
    with pytest.raises(SessionSourceError, match="no Codex state database"):
        find_codex_database(tmp_path)
