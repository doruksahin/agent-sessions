"""Verify version records and install each built distribution in isolation."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import tomllib


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", help="Release tag, when validating a release")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    project = tomllib.loads((root / "pyproject.toml").read_text())["project"]
    version = project["version"]
    manifest = json.loads((root / ".release-please-manifest.json").read_text())
    locked = tomllib.loads((root / "uv.lock").read_text())
    package = next(p for p in locked["package"] if p["name"] == project["name"])
    assert version == manifest["."] == package["version"], "Version records disagree"
    if args.tag:
        assert args.tag == f"v{version}", "Release tag disagrees with package version"
        changelog = (root / "CHANGELOG.md").read_text()
        assert f"## [{version}]" in changelog or f"## {version} (" in changelog

    dist = root / "dist"
    artifacts = sorted([*dist.glob("*.whl"), *dist.glob("*.tar.gz")])
    expected = {
        f"agent_sessions-{version}-py3-none-any.whl",
        f"agent_sessions-{version}.tar.gz",
    }
    assert {p.name for p in artifacts} == expected, "Unexpected distribution set"
    with tempfile.TemporaryDirectory(prefix="agent-sessions-release-") as temporary:
        work = Path(temporary)
        history = work / "history"
        history.mkdir()
        with sqlite3.connect(history / "state_1.sqlite") as connection:
            connection.execute(
                "CREATE TABLE threads "
                "(id TEXT, source TEXT, title TEXT, cwd TEXT, updated_at INTEGER)"
            )
            connection.execute(
                "INSERT INTO threads VALUES (?, ?, ?, ?, ?)",
                ("release-smoke", "cli", "Synthetic session", "/example", 0),
            )
        environment = dict(os.environ, CODEX_HOME=str(history))
        environment.pop("PYTHONPATH", None)
        environment.pop("VIRTUAL_ENV", None)
        for index, artifact in enumerate(artifacts):
            venv = work / f"venv-{index}"
            subprocess.run(
                ["uv", "venv", "--python", sys.executable, str(venv)], check=True
            )
            python = venv / "bin" / "python"
            subprocess.run(
                ["uv", "pip", "install", "--python", str(python), str(artifact)],
                check=True,
                cwd=work,
                env=environment,
            )
            installed = subprocess.check_output(
                [
                    str(python),
                    "-c",
                    "from importlib.metadata import version; "
                    "import agent_sessions.providers.claude; "
                    "print(version('agent-sessions'))",
                ],
                cwd=work,
                env=environment,
                text=True,
            ).strip()
            assert installed == version, "Installed metadata disagrees"
            result = subprocess.run(
                [
                    str(venv / "bin" / "agent-sessions"),
                    "list",
                    "--provider",
                    "codex",
                    "--limit",
                    "1",
                ],
                check=True,
                cwd=work,
                env=environment,
                capture_output=True,
                text=True,
            )
            assert not result.stderr, result.stderr
            assert json.loads(result.stdout) == [
                {
                    "provider": "codex",
                    "sessionId": "release-smoke",
                    "sessionTitle": "Synthetic session",
                    "sessionFirstPrompt": None,
                    "cwd": "/example",
                    "updatedAt": "1970-01-01T00:00:00.000Z",
                }
            ]
            print(f"Verified {artifact.name} on Python {sys.version.split()[0]}")
    (dist / "SHA256SUMS").write_text(
        "".join(
            f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n"
            for p in artifacts
        )
    )


if __name__ == "__main__":
    main()
