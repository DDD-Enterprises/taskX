"""Git branch guard helpers for TaskX assisted PR flow."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True)
class GitState:
    """Captured git checkout state for restore operations."""

    mode: str
    branch: str | None
    head_sha: str


class PreflightRefusal(RuntimeError):
    """Raised when preflight rails refuse command execution."""


@dataclass(frozen=True)
class PreflightFlags:
    """Toggle flags that relax refusal rails."""

    allow_dirty: bool
    allow_detached: bool
    allow_base_branch: bool
    base_branch: str


def _run_git(repo_root: Path, args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if check and completed.returncode != 0:
        stderr = (completed.stderr or completed.stdout).strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {stderr}")
    return completed


def capture_git_state(repo_root: Path) -> GitState:
    """Capture current branch/detached state and HEAD sha."""
    resolved = repo_root.resolve()
    branch = _run_git(resolved, ["rev-parse", "--abbrev-ref", "HEAD"], check=True).stdout.strip()
    head_sha = _run_git(resolved, ["rev-parse", "HEAD"], check=True).stdout.strip()

    if branch == "HEAD":
        return GitState(mode="detached", branch=None, head_sha=head_sha)
    return GitState(mode="branch", branch=branch, head_sha=head_sha)


def restore_git_state(repo_root: Path, state: GitState) -> None:
    """Restore checkout to captured state."""
    resolved = repo_root.resolve()
    if state.mode == "branch":
        if not state.branch:
            raise RuntimeError("Invalid git state: branch mode requires branch name")
        _run_git(resolved, ["checkout", state.branch], check=True)
        return

    _run_git(resolved, ["checkout", "--detach", state.head_sha], check=True)


def preflight_or_refuse(repo_root: Path, flags: PreflightFlags) -> GitState:
    """Validate repo state against refusal rails and return captured state."""
    resolved = repo_root.resolve()
    state = capture_git_state(resolved)

    status = _run_git(
        resolved,
        ["status", "--porcelain", "--untracked-files=all"],
        check=True,
    ).stdout.strip()

    if status and not flags.allow_dirty:
        raise PreflightRefusal("Refused: repository working tree is dirty (use --allow-dirty to override).")

    if state.mode == "detached" and not flags.allow_detached:
        raise PreflightRefusal("Refused: detached HEAD state (use --allow-detached to override).")

    if state.mode == "branch" and state.branch == flags.base_branch and not flags.allow_base_branch:
        raise PreflightRefusal(
            f"Refused: current branch is base branch `{flags.base_branch}` "
            "(use --allow-base-branch to override)."
        )

    return state
