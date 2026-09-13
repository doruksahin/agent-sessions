from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol


class SessionSourceError(RuntimeError):
    """A provider's local session metadata could not be read."""


@dataclass(frozen=True, slots=True)
class Session:
    provider: str
    session_id: str
    session_title: str
    session_first_prompt: str | None
    cwd: str | None
    updated_at: datetime

    def as_dict(self) -> dict[str, str | None]:
        return {
            "provider": self.provider,
            "sessionId": self.session_id,
            "sessionTitle": self.session_title,
            "sessionFirstPrompt": self.session_first_prompt,
            "cwd": self.cwd,
            "updatedAt": format_timestamp(self.updated_at),
        }


class SessionProvider(Protocol):
    def list_sessions(self, *, limit: int) -> list[Session]: ...


def collect_sessions(
    providers: Iterable[SessionProvider], *, limit: int
) -> list[Session]:
    sessions = [
        session
        for provider in providers
        for session in provider.list_sessions(limit=limit)
    ]
    sessions.sort(
        key=lambda session: (session.updated_at, session.session_id), reverse=True
    )
    return sessions[:limit]


def clean_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    return cleaned or None


def timestamp_from_milliseconds(value: int) -> datetime:
    return datetime.fromtimestamp(value / 1000, tz=UTC)


def format_timestamp(value: datetime) -> str:
    normalized = value.astimezone(UTC)
    return normalized.isoformat(timespec="milliseconds").replace("+00:00", "Z")
