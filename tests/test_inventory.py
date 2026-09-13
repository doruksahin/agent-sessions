from __future__ import annotations

from datetime import UTC, datetime

from agent_sessions.inventory import Session, collect_sessions


class FakeProvider:
    def __init__(self, sessions: list[Session]) -> None:
        self.sessions = sessions
        self.received_limit: int | None = None

    def list_sessions(self, *, limit: int) -> list[Session]:
        self.received_limit = limit
        return self.sessions[:limit]


def session(provider: str, session_id: str, minute: int) -> Session:
    return Session(
        provider=provider,
        session_id=session_id,
        session_title=session_id,
        session_first_prompt=None,
        cwd=None,
        updated_at=datetime(2026, 1, 1, 0, minute, tzinfo=UTC),
    )


def test_collect_sessions_sorts_and_applies_global_limit() -> None:
    codex = FakeProvider([session("codex", "older", 1), session("codex", "newest", 4)])
    claude = FakeProvider([session("claude", "middle", 3)])

    result = collect_sessions([codex, claude], limit=2)

    assert [item.session_id for item in result] == ["newest", "middle"]
    assert codex.received_limit == 2
    assert claude.received_limit == 2


def test_session_serializes_the_stable_json_shape() -> None:
    value = Session(
        provider="codex",
        session_id="session-1",
        session_title="A title",
        session_first_prompt="A prompt",
        cwd="/project",
        updated_at=datetime(2026, 1, 2, 3, 4, 5, 6000, tzinfo=UTC),
    )

    assert value.as_dict() == {
        "provider": "codex",
        "sessionId": "session-1",
        "sessionTitle": "A title",
        "sessionFirstPrompt": "A prompt",
        "cwd": "/project",
        "updatedAt": "2026-01-02T03:04:05.006Z",
    }
