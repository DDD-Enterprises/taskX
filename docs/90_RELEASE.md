<<<<<<< HEAD
# UV-Native Release Guide

This project ships with `uv` as the source of truth for local development, CI, and tagged releases.

## Version Discipline

- Follow semantic versioning.
- Update both `pyproject.toml` and `src/taskx/__init__.py` to the same version.
- Create tags as `vX.Y.Z`; release automation runs only from tags.

## Lockfile Strategy

- `uv.lock` is committed and reviewed.
- Update dependencies with `uv lock` and include lockfile diffs in PRs.
- Use `uv sync --all-extras --dev` in local verification and CI.

## Local Release Checklist

1. Ensure a clean working tree.
2. Sync environment:
   - `uv sync --all-extras --dev`
3. Run tests:
   - `uv run pytest`
4. Build artifacts:
   - `uv build`
5. Verify install from built wheel:
   - `python -m pip install --force-reinstall dist/*.whl`
   - `taskx --help`
6. Create and push release tag:
   - `git tag vX.Y.Z`
   - `git push origin vX.Y.Z`

## CI and Publish Workflow

- `.github/workflows/taskx_ci.yml` uses `astral-sh/setup-uv` and runs:
  - `uv sync --all-extras --dev`
  - `uv run ruff check src/taskx`
  - `uv run mypy src/taskx`
  - `uv run pytest`
  - `uv build` (Python 3.11 job)
- `.github/workflows/taskx_release.yml` runs on `v*` tags and executes:
  - `uv sync --all-extras --dev`
  - version consistency checks
  - `uv run pytest -q`
  - `uv build`
  - wheel install smoke test
  - `uv publish` when `PYPI_API_TOKEN` is configured

## Notes

- Release automation should fail fast on version mismatch.
- Packaging artifacts are produced by `uv build` only.
- Avoid parallel release tracks with mixed package managers.
=======
# Release Process (Maintainers)

This guide details the release process for TaskX maintainers.

## Release checklist

1. Update version
2. Changelog
3. Verify
4. Tag
5. Publish

## Preparing the release

### Bump version

Update the version string in two locations:

1. `src/taskx/__init__.py`
2. `pyproject.toml`

Commit these changes:

```bash
git add src/taskx/__init__.py pyproject.toml
git commit -m "chore: bump version to X.Y.Z"
```

### Verify locally

Run tests:

```bash
uv run pytest
```

Build artifacts:

```bash
uv build
```

Publish:

```bash
uv publish
```

If your repo uses a local release verification script, run it before tagging.

## Tagging and publishing

Create a tag matching your version (must start with `v`):

```bash
git tag vX.Y.Z
git push origin vX.Y.Z
```

Pushing a tag should trigger the release workflow in CI.

## Automated workflow

After pushing the tag, your GitHub Actions release workflow should:

1. Verify tag matches `pyproject.toml` version
2. Run tests in a clean environment
3. Build sdist and wheel
4. Smoke test install and `taskx --help`
5. Publish artifacts
>>>>>>> codex/TP-DOCS-STRUCTURE-0002-doc-spine
