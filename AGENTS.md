# Agent sessions

This repository owns the `agent-sessions` command. Keep stdout machine-readable: successful
commands emit only JSON, while diagnostics belong on stderr.

Read the [architecture guide](docs/architecture/README.md) before changing responsibilities,
interfaces, dependencies, execution or storage, or failure behavior.

Provider-specific storage knowledge stays in `src/agent_sessions/providers/`. Keep the shared
record and merge behavior in `inventory.py`, and keep argument parsing and output in `cli.py`.
Do not add an index, cache, transcript parser, or provider-independent abstraction without a
demonstrated requirement.

Use synthetic session metadata in tests. Never commit personal session databases, transcripts,
prompts, credentials, or absolute user paths.

Run `uv run pytest` after changes. For an installed-command smoke test, run
`uv run agent-sessions list --provider codex --limit 1` on a machine with Codex history.
