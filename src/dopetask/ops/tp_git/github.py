"""GitHub integrations for dopetask tp git commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from dopetask.ops.tp_git.exec import run_command, run_git
from dopetask.ops.tp_git.guards import resolve_repo_root
from dopetask.ops.tp_git.naming import build_worktree_path


def _ensure_gh_auth(repo_root: Path) -> None:
    auth = run_command(["gh", "auth", "status"], cwd=repo_root, check=False)
    if auth.returncode != 0:
        detail = (auth.stderr or auth.stdout).strip()
        raise RuntimeError(f"gh auth failed: {detail}")


def _worktree_for_tp(repo_root: Path, tp_id: str) -> Path:
    worktree_path = build_worktree_path(repo_root, tp_id)
    if not worktree_path.exists():
        raise RuntimeError(f"worktree does not exist: {worktree_path}")
    return worktree_path


def _branch_for_worktree(repo_root: Path, worktree_path: Path) -> str:
    out = run_git(["-C", str(worktree_path), "rev-parse", "--abbrev-ref", "HEAD"], repo_root=repo_root).stdout
    branch = out.strip()
    if not branch:
        raise RuntimeError(f"unable to resolve branch for worktree {worktree_path}")
    return branch


def _gh_pr_view(worktree_path: Path, *, check: bool = True) -> dict[str, Any]:
    viewed = run_command(
        [
            "gh",
            "pr",
            "view",
            "--json",
            "url,state,mergeStateStatus,autoMergeRequest",
        ],
        cwd=worktree_path,
        check=check,
    )
    if viewed.returncode != 0:
        detail = (viewed.stderr or viewed.stdout).strip()
        raise RuntimeError(f"gh pr view failed: {detail}")
    try:
        payload = json.loads(viewed.stdout)
        if not isinstance(payload, dict):
            raise RuntimeError("gh pr view returned non-dict JSON output")
        return payload
    except json.JSONDecodeError as exc:
        raise RuntimeError("gh pr view returned non-JSON output") from exc


def pr_create(
    *,
    tp_id: str,
    title: str,
    body: str | None = None,
    body_file: Path | None = None,
    repo: Path | None = None,
) -> dict[str, Any]:
    """Push TP branch and open PR via gh."""
    repo_root = resolve_repo_root(repo)
    _ensure_gh_auth(repo_root)

    worktree_path = _worktree_for_tp(repo_root, tp_id)
    branch = _branch_for_worktree(repo_root, worktree_path)

    run_git(["-C", str(worktree_path), "push", "-u", "origin", branch], repo_root=repo_root)

    cmd = ["gh", "pr", "create", "--title", title]
    if body_file is not None:
        cmd.extend(["--body-file", str(body_file.resolve())])
    elif body is not None:
        cmd.extend(["--body", body])
    created = run_command(cmd, cwd=worktree_path, check=False)
    if created.returncode != 0:
        detail = (created.stderr or created.stdout).strip()
        if "already exists" not in detail.lower():
            raise RuntimeError(f"gh pr create failed: {detail}")

    viewed = _gh_pr_view(worktree_path)
    viewed.update(
        {
            "repo_root": str(repo_root),
            "tp_id": tp_id,
            "branch": branch,
            "worktree_path": str(worktree_path),
        }
    )
    return viewed


def pr_status(*, tp_id: str, repo: Path | None = None) -> dict[str, Any]:
    """Return local/worktree status plus PR metadata if available."""
    repo_root = resolve_repo_root(repo)
    worktree_path = _worktree_for_tp(repo_root, tp_id)
    branch = _branch_for_worktree(repo_root, worktree_path)
    status_porcelain = run_git(["-C", str(worktree_path), "status", "--porcelain"], repo_root=repo_root).stdout

    payload: dict[str, Any] = {
        "repo_root": str(repo_root),
        "tp_id": tp_id,
        "worktree_path": str(worktree_path),
        "branch": branch,
        "dirty": bool(status_porcelain.strip()),
    }

    try:
        _ensure_gh_auth(repo_root)
        payload["pr"] = _gh_pr_view(worktree_path, check=True)
    except Exception as exc:
        payload["pr_error"] = str(exc)
    return payload


def merge_pr(
    *,
    tp_id: str,
    mode: str = "squash",
    repo: Path | None = None,
) -> dict[str, Any]:
    """Attempt auto-merge and fail closed when unsupported."""
    if mode not in {"squash", "merge", "rebase"}:
        raise RuntimeError(f"unsupported merge mode: {mode}")

    repo_root = resolve_repo_root(repo)
    _ensure_gh_auth(repo_root)
    worktree_path = _worktree_for_tp(repo_root, tp_id)

    merge_cmd = ["gh", "pr", "merge", "--auto", "--delete-branch", f"--{mode}"]
    merged = run_command(merge_cmd, cwd=worktree_path, check=False)
    if merged.returncode != 0:
        detail = (merged.stderr or merged.stdout).strip()
        instructions = (
            "Auto-merge could not be enabled. Manual steps:\n"
            "1) Review repository auto-merge and branch protection settings.\n"
            f"2) Re-run: gh pr merge --{mode} --delete-branch\n"
            "3) Confirm with: gh pr view --json url,state,autoMergeRequest,mergeStateStatus"
        )
        raise RuntimeError(f"merge failed: {detail}\n{instructions}")

    viewed = _gh_pr_view(worktree_path)
    viewed.update(
        {
            "repo_root": str(repo_root),
            "tp_id": tp_id,
            "worktree_path": str(worktree_path),
            "mode": mode,
        }
    )
    return viewed
