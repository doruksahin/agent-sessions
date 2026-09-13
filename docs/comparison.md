# CLI application or agent plugin?

`agent-sessions` is a CLI application because its primary interface is a non-interactive command
whose JSON output is consumed directly by people, shell scripts, and tools such as `jq`.

## Comparison

| Concern | Current CLI application | Native agent plugin |
| --- | --- | --- |
| Primary caller | A person or shell process | A Codex or Claude Code agent |
| Entry point | `agent-sessions list` | A host-specific skill invocation |
| Output path | JSON is written directly to stdout | Results pass through an agent response |
| Shell composition | Pipes directly into `jq` or another command | Requires the agent to invoke and preserve CLI output |
| Provider access | Codex SQLite adapter and Claude Agent SDK adapter | The same adapters would still be required |
| Distribution | One Python package and executable | Host manifests, skill instructions, and plugin installation |
| Current value | Implements the requested terminal workflow | Adds packaging without adding session-discovery behavior |

Plugin packaging does not provide another source of session metadata. A plugin would still call
the same inventory implementation, so it would add a second invocation layer without simplifying
the Codex or Claude adapters.

## Current module shape

```text
terminal
   |
   v
cli.py -> inventory.py -> providers/codex.py  -> Codex SQLite
                       -> providers/claude.py -> Claude Agent SDK
```

The provider interface is a real seam because two implementations vary behind it. The CLI remains
the only public interface; provider selection, combined ordering, and the global limit stay behind
that interface.

## When plugin packaging would be justified

Reconsider a plugin if invoking the inventory from inside Codex or Claude Code becomes a required
workflow—for example, if an agent must select a prior session before continuing a task. The plugin
should then be a thin wrapper around the installed CLI rather than a second session reader.

Until that requirement exists, the application deliberately has no plugin manifests, skills,
session index, cache, transcript parser, or live-state inference.

## Verify the decision against the implementation

- [`cli.py`](../src/agent_sessions/cli.py) owns the command arguments and JSON serialization.
- [`inventory.py`](../src/agent_sessions/inventory.py) owns normalization, ordering, and limiting.
- [`codex.py`](../src/agent_sessions/providers/codex.py) owns read-only Codex access.
- [`claude.py`](../src/agent_sessions/providers/claude.py) owns Claude SDK access.
- The [architecture guide](architecture/README.md) records the repository responsibility and
  explicit non-goals.
