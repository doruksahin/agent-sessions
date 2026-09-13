# agent-sessions

`agent-sessions` lists local Codex and Claude Code sessions as normalized JSON. It is designed
for non-interactive shell use and composition with tools such as `jq`.

The command reads metadata from existing local history stores. It does not build an index,
modify histories, or parse complete transcripts.

See the [architecture guide](docs/architecture/README.md) for responsibilities, interfaces,
dependencies, storage, and failure behavior.

See [CLI application or agent plugin?](docs/comparison.md) for the comparison behind the
terminal-first design and the condition that would justify adding plugin packaging later.

## Install

Python 3.11 or newer and [uv](https://docs.astral.sh/uv/) are required for development:

```sh
uv sync --locked
```

To install the command as a standalone tool from a checkout:

```sh
uv tool install .
```

## Use

List the 100 most recently updated sessions across both providers:

```sh
agent-sessions list
```

Select a provider or request a smaller result:

```sh
agent-sessions list --provider codex --limit 20
agent-sessions list --provider claude --limit 20
```

The limit applies after results from the selected providers are combined. It defaults to 100
and cannot exceed 100.

Filter or format the JSON with `jq`:

```sh
agent-sessions list --limit 100 |
  jq -r '.[] | [.provider, .sessionId, .sessionTitle, .cwd] | @tsv'
```

Each entry has the same shape:

```json
{
  "provider": "codex",
  "sessionId": "00000000-0000-4000-8000-000000000001",
  "sessionTitle": "Investigate session listing",
  "sessionFirstPrompt": "List recent local sessions.",
  "cwd": "/path/to/project",
  "updatedAt": "2026-09-13T12:34:56.000Z"
}
```

`sessionFirstPrompt` and `cwd` can be `null` when a provider has no value. Results are sorted by
`updatedAt` descending. A provider failure is reported on stderr and exits nonzero, so stdout is
never a misleading partial result.

## Data sources

- Codex: the newest numbered `state_*.sqlite` database under `CODEX_HOME` or `~/.codex`.
  Only top-level CLI and desktop/editor sessions are included; subagent records are excluded.
- Claude Code: the official `claude-agent-sdk` `list_sessions()` interface.

The installed Claude SDK version is controlled by this repository's lockfile. The tool reads
local session metadata and never writes to either provider's history.

## Develop

```sh
uv run pytest
```
