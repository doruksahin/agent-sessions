from __future__ import annotations

from collections.abc import Callable
from typing import Any

from agent_sessions.inventory import (
    Session,
    SessionSourceError,
    clean_text,
    timestamp_from_milliseconds,
)

SessionLoader = Callable[..., list[Any]]


class ClaudeSessionProvider:
    def __init__(self, loader: SessionLoader | None = None) -> None:
        self._loader = loader

    def list_sessions(self, *, limit: int) -> list[Session]:
        loader = self._loader or _sdk_loader()
        try:
            results = loader(limit=limit)
            return [_session_from_sdk(value) for value in results]
        except SessionSourceError:
            raise
        except Exception as exc:
            raise SessionSourceError("cannot read Claude Code sessions") from exc


def _sdk_loader() -> SessionLoader:
    try:
        from claude_agent_sdk import list_sessions
    except (ImportError, AttributeError) as exc:
        raise SessionSourceError(
            "claude-agent-sdk 0.2.152 or newer is required to list Claude sessions"
        ) from exc
    return list_sessions


def _session_from_sdk(value: Any) -> Session:
    session_id = str(value.session_id)
    first_prompt = clean_text(getattr(value, "first_prompt", None))
    title = (
        clean_text(getattr(value, "custom_title", None))
        or clean_text(getattr(value, "summary", None))
        or first_prompt
        or session_id
    )
    return Session(
        provider="claude",
        session_id=session_id,
        session_title=title,
        session_first_prompt=first_prompt,
        cwd=clean_text(getattr(value, "cwd", None)),
        updated_at=timestamp_from_milliseconds(int(value.last_modified)),
    )
