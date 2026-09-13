from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from agent_sessions.inventory import (
    SessionProvider,
    SessionSourceError,
    collect_sessions,
)
from agent_sessions.providers.claude import ClaudeSessionProvider
from agent_sessions.providers.codex import CodexSessionProvider

DEFAULT_LIMIT = 100
MAX_LIMIT = 100


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent-sessions",
        description="List local Codex and Claude Code sessions as JSON.",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)
    list_parser = subcommands.add_parser("list", help="list local sessions")
    list_parser.add_argument(
        "--provider",
        choices=("all", "codex", "claude"),
        default="all",
        help="session provider to list (default: all)",
    )
    list_parser.add_argument(
        "--limit",
        type=_bounded_limit,
        default=DEFAULT_LIMIT,
        metavar="N",
        help=f"maximum combined results, 1-{MAX_LIMIT} (default: {DEFAULT_LIMIT})",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        providers = _providers_for(arguments.provider)
        sessions = collect_sessions(providers, limit=arguments.limit)
        json.dump(
            [session.as_dict() for session in sessions],
            sys.stdout,
            ensure_ascii=False,
            indent=2,
        )
        sys.stdout.write("\n")
    except SessionSourceError as exc:
        print(f"agent-sessions: {exc}", file=sys.stderr)
        return 1
    except BrokenPipeError:
        return 0
    return 0


def _providers_for(provider: str) -> list[SessionProvider]:
    if provider == "codex":
        return [CodexSessionProvider()]
    if provider == "claude":
        return [ClaudeSessionProvider()]
    return [CodexSessionProvider(), ClaudeSessionProvider()]


def _bounded_limit(value: str) -> int:
    try:
        limit = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if not 1 <= limit <= MAX_LIMIT:
        raise argparse.ArgumentTypeError(f"must be between 1 and {MAX_LIMIT}")
    return limit


if __name__ == "__main__":
    raise SystemExit(main())
