"""WIP rescue patch helpers for repo-guard failures."""

from __future__ import annotations

import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path


def _resolve_rescue_patch_path(cwd: Path, rescue_patch: str) -> Path:
    """Resolve explicit path or 'auto' destination for rescue patch output."""
    if rescue_patch == "auto":
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        return cwd / "out" / "taskx_rescue" / timestamp / "rescue.patch"

    candidate = Path(rescue_patch).expanduser()
    if not candidate.is_absolute():
        candidate = cwd / candidate
    return candidate


def _run_git_text(repo_root: Path, args: list[str]) -> str:
    """Run a git command and return stdout as text."""
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        capture_output=True,
        check=False,
        text=True,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip() or "unknown git error"
        raise RuntimeError(f"Unable to generate rescue patch: git {' '.join(args)} failed: {stderr}")
    return result.stdout


def write_rescue_patch(*, repo_root: Path, cwd: Path, rescue_patch: str) -> Path:
    """
    Write a rescue patch containing only `git status --porcelain` and `git diff`.

    Args:
        repo_root: Git repository root for diff capture
        cwd: Working directory where command was attempted
        rescue_patch: Destination path or the literal string "auto"

    Returns:
        Absolute path to the written rescue patch
    """
    output_path = _resolve_rescue_patch_path(cwd=cwd, rescue_patch=rescue_patch)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    status_text = _run_git_text(repo_root, ["status", "--porcelain"])
    diff_text = _run_git_text(repo_root, ["diff"])
    patch_text = (
        "git status --porcelain\n"
        f"{status_text}\n"
        "git diff\n"
        f"{diff_text}"
    )

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=output_path.parent,
        delete=False,
    ) as handle:
        handle.write(patch_text)
        temp_path = Path(handle.name)

    temp_path.replace(output_path)
    return output_path
