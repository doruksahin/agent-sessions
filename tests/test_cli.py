from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from agent_sessions import cli
from agent_sessions.inventory import Session, SessionSourceError


class FakeProvider:
    def list_sessions(self, *, limit: int) -> list[Session]:
        return [
            Session(
                provider="codex",
                session_id="session-1",
                session_title="A title",
                session_first_prompt="A prompt",
                cwd="/project",
                updated_at=datetime(2026, 1, 1, tzinfo=UTC),
            )
        ]


def test_cli_defaults_to_all_providers_and_one_hundred_results() -> None:
    arguments = cli.build_parser().parse_args(["list"])

    assert arguments.provider == "all"
    assert arguments.limit == 100


def test_cli_writes_only_json_to_stdout(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli, "_providers_for", lambda provider: [FakeProvider()])

    exit_code = cli.main(["list", "--provider", "codex", "--limit", "1"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.err == ""
    assert json.loads(captured.out) == [
        {
            "provider": "codex",
            "sessionId": "session-1",
            "sessionTitle": "A title",
            "sessionFirstPrompt": "A prompt",
            "cwd": "/project",
            "updatedAt": "2026-01-01T00:00:00.000Z",
        }
    ]


def test_cli_reports_provider_failure_on_stderr(monkeypatch, capsys) -> None:
    class BrokenProvider:
        def list_sessions(self, *, limit: int) -> list[Session]:
            raise SessionSourceError("history unavailable")

    monkeypatch.setattr(cli, "_providers_for", lambda provider: [BrokenProvider()])

    exit_code = cli.main(["list"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == "agent-sessions: history unavailable\n"


@pytest.mark.parametrize("value", ["0", "101", "not-a-number"])
def test_cli_rejects_invalid_limits(value: str) -> None:
    with pytest.raises(SystemExit) as result:
        cli.build_parser().parse_args(["list", "--limit", value])

    assert result.value.code == 2
