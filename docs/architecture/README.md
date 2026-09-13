# agent-sessions architecture

## Responsibility

This repository owns a local, read-only session inventory for Codex and Claude Code. It normalizes
provider metadata for terminal consumers. Codex and Claude own their history formats; this
repository does not index histories, modify sessions, infer live state, or bind sessions to tasks.

## Interfaces

The public interface is `agent-sessions list`, with optional `--provider` and `--limit` arguments.
It writes one JSON array containing normalized session metadata to stdout. The complete command and
output contract lives in the [README](../../README.md#use).

## Dependencies

The [package manifest](../../pyproject.toml) installs the official `claude-agent-sdk` for Claude
metadata. Codex access uses Python's built-in SQLite support. The application has no dependency on
the session-marking plugin, a history index, or another repository in the grouped workspace.

## Execution and storage

The command runs locally on Python 3.11 or newer. The
[Codex adapter](../../src/agent_sessions/providers/codex.py) opens the newest numbered Codex state
database in read-only mode. The [Claude adapter](../../src/agent_sessions/providers/claude.py) asks
the SDK for local session metadata. The application creates no database, cache, or session store.

## Failure behavior

An unavailable or incompatible requested provider stops the command with a nonzero status and a
diagnostic on stderr. It does not emit a partial JSON result. Invalid limits are rejected before a
provider is read, and a successful command keeps stdout valid JSON.

## Current implementation

The [CLI](../../src/agent_sessions/cli.py) owns arguments and serialization. The
[inventory module](../../src/agent_sessions/inventory.py) owns the normalized record, combined
ordering, and global limit. Provider-specific storage knowledge remains in the
[Codex](../../src/agent_sessions/providers/codex.py) and
[Claude](../../src/agent_sessions/providers/claude.py) adapters.

## Planned changes

No additional interfaces, providers, indexes, or plugin packaging are planned in this rollout.

## Decisions

Repository adoption follows the
[shared architecture standard](https://github.com/doruksahin/plugin-architecture/blob/main/standard/README.md).
Workspace registration and pinning follow the
[workspace guide](https://github.com/doruksahin/agent-workflows/blob/main/docs/workspace.md).
There is no repository-specific ADR for this initial implementation.

## Verification

Run `uv run --locked pytest` for behavior and `python3 .architecture/check.py --root .` for the
local contract. Check local documentation links with:

```sh
lychee --config .lychee.toml --offline './*.md' './docs/**/*.md' './.architecture/**/*.md'
```

The
[behavior CI](../../.github/workflows/ci.yml) and
[architecture CI](../../.github/workflows/architecture.yml) run those checks. Authenticated
network-link and cross-repository model checks remain maintainer verification under the shared
architecture procedure.
