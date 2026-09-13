from __future__ import annotations

from types import SimpleNamespace

import pytest

from agent_sessions.inventory import SessionSourceError
from agent_sessions.providers.claude import ClaudeSessionProvider


def test_claude_maps_sdk_results_and_title_fallbacks() -> None:
    received: dict[str, int] = {}

    def loader(*, limit: int):
        received["limit"] = limit
        return [
            SimpleNamespace(
                session_id="custom",
                custom_title="Chosen title",
                summary="Summary",
                first_prompt="First prompt",
                cwd="/project",
                last_modified=2000,
            ),
            SimpleNamespace(
                session_id="summary",
                custom_title=None,
                summary="Summary title",
                first_prompt=None,
                cwd=None,
                last_modified=1000,
            ),
            SimpleNamespace(
                session_id="prompt",
                custom_title=" ",
                summary="",
                first_prompt="Prompt title",
                cwd=" ",
                last_modified=0,
            ),
        ]

    result = ClaudeSessionProvider(loader).list_sessions(limit=3)

    assert received == {"limit": 3}
    assert [item.session_title for item in result] == [
        "Chosen title",
        "Summary title",
        "Prompt title",
    ]
    assert result[1].session_first_prompt is None
    assert result[2].cwd is None


def test_claude_wraps_sdk_failures() -> None:
    def loader(*, limit: int):
        raise OSError("broken history")

    with pytest.raises(SessionSourceError, match="cannot read Claude Code sessions"):
        ClaudeSessionProvider(loader).list_sessions(limit=1)
