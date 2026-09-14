# Releases

[Release Please](../release-please-config.json) prepares a release PR from conventional commits
on `main`. Its Python strategy updates `pyproject.toml` and `CHANGELOG.md`; the configured TOML
updater changes only this project's version in `uv.lock`. The
[manifest](../.release-please-manifest.json) records the same version. Use `fix:` for patches,
`feat:` for minor releases, and a breaking-change footer for incompatible changes. Before 1.0,
breaking changes increment the minor version.

The lockfile selector uses `name.value` because Release Please's TOML updater wraps scalar
values while preserving their text positions. Validate the generated lockfile with `uv --locked`
checks when updating Release Please.

Review and merge the generated PR. The [release workflow](../.github/workflows/release.yml)
creates its `vX.Y.Z` GitHub release, checks out the tag, runs the Python 3.11 and 3.13 checks,
builds the wheel and source archive, and smoke-installs both in fresh environments using
synthetic history. It uploads those exact distributions and `SHA256SUMS`. Publication does
not upgrade an installed command.

Repository Actions settings must allow GitHub Actions to create pull requests. The workflow
grants its built-in token contents, issues, and pull-request write permissions for preparation.
Artifacts are uploaded in the same workflow: releases created by the built-in token do not
trigger a separate release-event workflow. Such release PRs may not trigger ordinary PR CI;
run the checks below before merging, and the publication job repeats the behavior and package
checks on the tag. A GitHub release without its three assets is incomplete.

## Local checks and manual recovery

If hosted jobs cannot start, including account billing or spending-limit failures, record that
limitation on the PR/release and run the same checks locally. Do not treat an unstarted job as
a passing check. Respect enforced branch protections.

With an authenticated GitHub CLI, run the pinned release tooling using a token supplied through
the environment (never place it in source or logs):

```sh
export GITHUB_TOKEN="$(gh auth token)"
npx --yes release-please@17.11.2 release-pr --repo-url doruksahin/agent-sessions
```

Review the generated PR and check its exact commit in this checkout:

```sh
for version in 3.11 3.13; do
  uv run --locked --python "$version" ruff check .
  uv run --locked --python "$version" ruff format --check .
  uv run --locked --python "$version" pytest
done
python3 .architecture/check.py --root .
actionlint
lychee --config .lychee.toml --offline './*.md' './docs/**/*.md' './.architecture/**/*.md'
uv build --no-sources
uv run --locked --python 3.11 python tools/check-release.py
uv run --locked --python 3.13 python tools/check-release.py
```

After merging, repeat the checks on the exact merged commit, then create the release through
Release Please so its tag, release notes, and PR labels remain consistent:

```sh
npx --yes release-please@17.11.2 github-release --repo-url doruksahin/agent-sessions
```

Set `RELEASE_TAG` to the resulting tag. Verify it points to the checked commit; validate and
upload the distributions built from that commit:

```sh
git fetch origin --tags
test "$(git rev-parse HEAD)" = "$(git rev-parse "$RELEASE_TAG^{commit}")"
uv run --locked --python 3.11 python tools/check-release.py --tag "$RELEASE_TAG"
uv run --locked --python 3.13 python tools/check-release.py --tag "$RELEASE_TAG"
gh release upload "$RELEASE_TAG" dist/*.whl dist/*.tar.gz dist/SHA256SUMS
```

Download the published assets to a fresh directory, verify `SHA256SUMS`, and smoke-install the
downloaded wheel and source archive. Once hosted jobs are available, a manual workflow dispatch
with the existing tag can publish missing artifacts without preparing another release. Uploads
refuse to overwrite existing assets; after a partial upload, compare downloaded checksums and
upload only missing files from the verified build. Never replace a published version's contents.
