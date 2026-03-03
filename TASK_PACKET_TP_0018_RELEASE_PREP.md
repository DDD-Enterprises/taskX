# TASK_PACKET TP_0018 — Release Prep Version Bump And Notes

## GOAL
Prepare the next dopeTask release without guessing by inspecting the current repo state, using the existing release workflow as the source of truth, drafting release notes from evidence, and updating the version and release docs consistently.

## SCOPE (ALLOWLIST)
- `CHANGELOG.md`
- `pyproject.toml`
- `src/dopetask/__init__.py`
- `docs/90_RELEASE.md`
- `docs/RELEASE.md`

## NON-NEGOTIABLES
- Inspect the current release path before editing: `docs/90_RELEASE.md`, `docs/RELEASE.md`, `.github/workflows/release.yml`, `scripts/release.sh`, and `scripts/taskx_release_local.sh` are the evidence base.
- Do not guess the next version number. Derive the bump from repo evidence and record the rationale in the Implementer Report.
- Keep the version synchronized in every source of truth touched by this packet.
- Do not change release automation behavior unless a direct docs/version inconsistency forces a docs update within the allowlist.
- Use the local `changelog-generator` skill to draft release notes from git history before finalizing `CHANGELOG.md`.
- Keep edits minimal and release-focused. No unrelated cleanup.

## REQUIRED CHANGES
1. Inspect the repository state and current release process, identifying the authoritative version locations and the actual tag-gated release path.
2. Determine the next release version from evidence already in the repository, including the current version, unreleased changelog state, and release workflow expectations.
3. Update `CHANGELOG.md` so the next release entry is evidence-based and aligned with the chosen version.
4. Bump the version consistently in `pyproject.toml` and `src/dopetask/__init__.py`.
5. Update `docs/90_RELEASE.md` and `docs/RELEASE.md` only as needed to match the current release workflow and avoid process drift.
6. Produce an Implementer Report that states the version chosen, why that bump was selected, what release-process evidence was used, and whether any release-doc drift remained out of scope.

## VERIFICATION COMMANDS
```bash
uv run pytest
uv build
python -c "import pathlib, re; py = re.search(r'^version = \"([^\"]+)\"$', pathlib.Path('pyproject.toml').read_text(), re.M); init = re.search(r'^__version__ = \"([^\"]+)\"$', pathlib.Path('src/dopetask/__init__.py').read_text(), re.M); assert py and init and py.group(1) == init.group(1), (py.group(1) if py else None, init.group(1) if init else None); print(py.group(1))"
uv run dopetask --version
```

## DEFINITION OF DONE
- The next release version is selected from repo evidence, not guesswork.
- `CHANGELOG.md`, `pyproject.toml`, and `src/dopetask/__init__.py` agree on the release state required by this packet.
- Release documentation reflects the current tag-gated workflow without introducing drift.
- All verification commands pass.
- The Implementer Report includes exact commands run, raw outputs, the release bump rationale, and explicit stop-condition confirmation.

## SOURCES
- `CHANGELOG.md`
- `pyproject.toml`
- `src/dopetask/__init__.py`
- `docs/90_RELEASE.md`
- `docs/RELEASE.md`
- `.github/workflows/release.yml`
- `scripts/release.sh`
- `scripts/taskx_release_local.sh`

## COMMIT PLAN
```json
{
  "commit_plan": [
    {
      "step_id": "C1",
      "message": "docs(release): update release notes and process docs",
      "allowlist": [
        "CHANGELOG.md",
        "docs/90_RELEASE.md",
        "docs/RELEASE.md"
      ],
      "verify": [
        "uv run pytest"
      ]
    },
    {
      "step_id": "C2",
      "message": "chore(release): bump version",
      "allowlist": [
        "pyproject.toml",
        "src/dopetask/__init__.py"
      ],
      "verify": [
        "uv build",
        "python -c \"import pathlib, re; py = re.search(r'^version = \\\"([^\\\"]+)\\\"$', pathlib.Path('pyproject.toml').read_text(), re.M); init = re.search(r'^__version__ = \\\"([^\\\"]+)\\\"$', pathlib.Path('src/dopetask/__init__.py').read_text(), re.M); assert py and init and py.group(1) == init.group(1), (py.group(1) if py else None, init.group(1) if init else None); print(py.group(1))\"",
        "uv run dopetask --version"
      ]
    }
  ]
}
```
