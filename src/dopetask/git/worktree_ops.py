"""Worktree lifecycle helpers for deterministic dopeTask commit sequencing."""

from __future__ import annotations

import json
import re
import shlex
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

__all__ = ["start_worktree", "commit_sequence", "finish_run"]


@dataclass(frozen=True)
class CommitPlanStep:
    """One commit-plan step parsed from TASK_PACKET.md."""

    step_id: str
    message: str
    allowlist: list[str]
    verify: list[str]


def _timestamp_utc() -> str:
    """Return current UTC timestamp in RFC3339 Z format."""
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _normalize_repo_path(path: str) -> str:
    """Normalize path values to git-status style repo-relative paths."""
    normalized = path.strip().replace("\\", "/")
    normalized = normalized.removeprefix("./")
    return normalized


def _run_git(
    args: list[str],
    *,
    cwd: Path,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Run a git command and return completed process."""
    completed = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )
    if check and completed.returncode != 0:
        stderr = (completed.stderr or completed.stdout).strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {stderr}")
    return completed


def _git_output(args: list[str], *, cwd: Path) -> str:
    """Run git command and return stdout."""
    return _run_git(args, cwd=cwd, check=True).stdout.strip()


def _git_repo_root(cwd: Path) -> Path:
    """Resolve git repository root."""
    return Path(_git_output(["rev-parse", "--show-toplevel"], cwd=cwd))


def _git_current_branch(repo_root: Path) -> str:
    """Return active branch name."""
    return _git_output(["rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_root)


def _git_status_porcelain(repo_root: Path) -> list[str]:
    """Return porcelain status lines."""
    completed = _run_git(
        ["status", "--porcelain", "--untracked-files=all"],
        cwd=repo_root,
        check=True,
    )
    output = completed.stdout
    if not output.strip():
        return []
    return [line for line in output.splitlines() if line]


def _status_paths(status_lines: list[str]) -> set[str]:
    """Extract file paths from porcelain status lines."""
    paths: set[str] = set()
    for line in status_lines:
        if len(line) < 4:
            continue
        path = line[3:]
        # Rename format: old -> new
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        paths.add(_normalize_repo_path(path))
    return paths


def _has_staged_changes(status_lines: list[str]) -> bool:
    """True when status contains staged entries."""
    for line in status_lines:
        if len(line) < 2:
            continue
        x = line[0]
        if x not in {" ", "?"}:
            return True
    return False


def _append_dirty_state(
    *,
    run_dir: Path,
    location: str,
    policy: str,
    stash_ref: str,
    message: str,
    status_porcelain: list[str],
) -> None:
    """Append one stash event record to DIRTY_STATE.json."""
    dirty_state_path = run_dir / "DIRTY_STATE.json"
    entries: list[dict[str, Any]]
    if dirty_state_path.exists():
        try:
            payload = json.loads(dirty_state_path.read_text(encoding="utf-8"))
            entries = payload if isinstance(payload, list) else []
        except json.JSONDecodeError:
            entries = []
    else:
        entries = []

    entries.append(
        {
            "schema_version": "1.0",
            "location": location,
            "policy": policy,
            "stash_ref": stash_ref,
            "message": message,
            "status_porcelain": sorted(status_porcelain),
            "timestamp_utc": _timestamp_utc(),
        }
    )
    dirty_state_path.parent.mkdir(parents=True, exist_ok=True)
    dirty_state_path.write_text(
        json.dumps(entries, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _stash_changes(
    *,
    repo_root: Path,
    message: str,
    include_ignored: bool,
    paths: list[str] | None = None,
) -> str:
    """Stash changes and return created stash reference."""
    args = ["stash", "push", "-m", message]
    if include_ignored:
        args.append("--all")
    else:
        args.append("--include-untracked")

    if paths:
        args.append("--")
        args.extend(paths)

    result = _run_git(args, cwd=repo_root, check=True)
    if "No local changes to save" in result.stdout:
        raise RuntimeError("No local changes to stash")

    stash_ref = _git_output(["stash", "list", "-n", "1", "--format=%gd"], cwd=repo_root)
    if not stash_ref:
        raise RuntimeError("Failed to determine created stash reference")
    return stash_ref


def _sanitize_token(value: str) -> str:
    """Make deterministic token from run/branch names."""
    token = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip()).strip("-").lower()
    return token or "run"


def _default_branch(run_dir: Path) -> str:
    """Infer default task branch from run directory name."""
    return f"tp/{_sanitize_token(run_dir.name)}"


def _load_packet_identity_tokens(run_dir: Path) -> tuple[str | None, str | None]:
    """Best-effort extraction of packet_id and project_id from TASK_PACKET.md."""
    task_packet_path = run_dir / "TASK_PACKET.md"
    if not task_packet_path.exists():
        return None, None

    try:
        content = task_packet_path.read_text(encoding="utf-8")
    except OSError:
        return None, None

    packet_id: str | None = None
    first_line = content.splitlines()[0] if content.splitlines() else ""
    first_line_match = re.match(r"^#\s+TASK_PACKET\s+(TP_\d{4})\b", first_line)
    if first_line_match is not None:
        packet_id = first_line_match.group(1)

    project_id: str | None = None
    section_match = re.search(
        r"^##\s+PROJECT IDENTITY\s*$\n(.*?)(?=^##\s+|\Z)",
        content,
        flags=re.MULTILINE | re.DOTALL,
    )
    if section_match is not None:
        for raw_line in section_match.group(1).splitlines():
            line = raw_line.strip()
            if line.startswith("-") or line.startswith("*"):
                line = re.sub(r"^[-*]\s+", "", line).strip()
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            if key.strip().lower() == "project_id":
                candidate = value.strip()
                if candidate:
                    project_id = candidate
                break

    return packet_id, project_id


def _identity_default_branch(run_dir: Path) -> str:
    """Infer canonical project-bound branch name when packet identity is available."""
    packet_id, project_id = _load_packet_identity_tokens(run_dir)
    if not project_id:
        return _default_branch(run_dir)

    run_slug = _sanitize_token(run_dir.name)
    project_slug = _sanitize_token(project_id)
    if packet_id:
        packet_slug = _sanitize_token(packet_id)
        return f"tp/{project_slug}/{packet_slug}-{run_slug}"
    return f"tp/{project_slug}/{run_slug}"


def _default_worktree_path(repo_root: Path, branch: str) -> Path:
    """Infer default worktree path."""
    folder = branch.replace("/", "_").replace("-", "_")
    return (repo_root / "out" / "worktrees" / folder).resolve()


def _load_commit_plan(task_packet_path: Path) -> list[CommitPlanStep]:
    """Parse COMMIT PLAN section from Task Packet markdown."""
    if not task_packet_path.exists():
        raise RuntimeError(f"Task packet not found: {task_packet_path}")

    content = task_packet_path.read_text(encoding="utf-8")
    section_match = re.search(
        r"^##\s+COMMIT PLAN\s*$\n(.*?)(?=^##\s+|\Z)",
        content,
        flags=re.MULTILINE | re.DOTALL,
    )
    if not section_match:
        raise RuntimeError("Task packet missing required COMMIT PLAN section")

    section = section_match.group(1)
    code_match = re.search(
        r"```json\s*(.*?)\s*```",
        section,
        flags=re.DOTALL,
    )
    if not code_match:
        raise RuntimeError("COMMIT PLAN section must contain a fenced json block")

    try:
        payload = json.loads(code_match.group(1))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid COMMIT PLAN JSON: {exc}") from exc

    raw_steps = payload.get("commit_plan")
    if not isinstance(raw_steps, list) or not raw_steps:
        raise RuntimeError("COMMIT PLAN must define a non-empty commit_plan array")

    steps: list[CommitPlanStep] = []
    for idx, raw in enumerate(raw_steps, start=1):
        if not isinstance(raw, dict):
            raise RuntimeError(f"COMMIT PLAN step {idx} must be an object")
        step_id = str(raw.get("step_id", "")).strip()
        message = str(raw.get("message", "")).strip()
        allowlist_raw = raw.get("allowlist")
        verify_raw = raw.get("verify", [])

        if not step_id:
            raise RuntimeError(f"COMMIT PLAN step {idx} missing step_id")
        if not message:
            raise RuntimeError(f"COMMIT PLAN step {step_id} missing message")
        if not isinstance(allowlist_raw, list) or not allowlist_raw:
            raise RuntimeError(f"COMMIT PLAN step {step_id} must include non-empty allowlist")
        if not isinstance(verify_raw, list):
            raise RuntimeError(f"COMMIT PLAN step {step_id} verify must be a list")

        allowlist = [_normalize_repo_path(str(p)) for p in allowlist_raw if str(p).strip()]
        if not allowlist:
            raise RuntimeError(f"COMMIT PLAN step {step_id} allowlist is empty after normalization")

        verify = [str(cmd).strip() for cmd in verify_raw if str(cmd).strip()]
        steps.append(
            CommitPlanStep(
                step_id=step_id,
                message=message,
                allowlist=allowlist,
                verify=verify,
            )
        )

    return steps


def _run_verify_commands(repo_root: Path, commands: list[str]) -> list[dict[str, Any]]:
    """Execute step verification commands in order."""
    results: list[dict[str, Any]] = []
    for command in commands:
        proc = subprocess.run(
            command,
            cwd=repo_root,
            shell=True,
            check=False,
            text=True,
            capture_output=True,
        )
        entry = {
            "command": command,
            "exit_code": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }
        results.append(entry)
        if proc.returncode != 0:
            escaped = shlex.quote(command)
            raise RuntimeError(f"Verification failed: {escaped}")
    return results


def _ensure_not_dirty_or_stash_all(
    *,
    repo_root: Path,
    run_dir: Path,
    dirty_policy: str,
    stash_message: str,
    location: str,
) -> None:
    """Enforce dirty policy for full-worktree operations."""
    status_lines = _git_status_porcelain(repo_root)
    if not status_lines:
        return
    if dirty_policy == "refuse":
        raise RuntimeError(
            "ERROR: repository working tree is dirty.\n"
            "Run with --dirty-policy stash to stash changes, or clean manually."
        )

    stash_ref = _stash_changes(
        repo_root=repo_root,
        message=stash_message,
        include_ignored=True,
    )
    _append_dirty_state(
        run_dir=run_dir,
        location=location,
        policy="stash",
        stash_ref=stash_ref,
        message=stash_message,
        status_porcelain=status_lines,
    )


def start_worktree(
    *,
    run_dir: Path,
    branch: str | None,
    base: str,
    remote: str,
    worktree_path: Path | None,
    dirty_policy: str,
    cwd: Path | None = None,
) -> dict[str, Any]:
    """Create dopeTask worktree + branch and write WORKTREE.json."""
    invoke_cwd = (cwd or Path.cwd()).resolve()
    repo_root = _git_repo_root(invoke_cwd)
    run_dir = run_dir.resolve()
    run_dir.mkdir(parents=True, exist_ok=True)

    _ensure_not_dirty_or_stash_all(
        repo_root=repo_root,
        run_dir=run_dir,
        dirty_policy=dirty_policy,
        stash_message=f"dopetask:wt-start:{run_dir.name}",
        location="repo_root",
    )

    selected_branch = branch.strip() if branch else _identity_default_branch(run_dir)
    branch_check = _run_git(
        ["show-ref", "--verify", "--quiet", f"refs/heads/{selected_branch}"],
        cwd=repo_root,
        check=False,
    )
    if branch_check.returncode == 0:
        raise RuntimeError(
            f"ERROR: branch '{selected_branch}' already exists.\n"
            "Refusing to reuse branch for deterministic execution."
        )

    selected_worktree_path = (
        worktree_path.expanduser().resolve()
        if worktree_path is not None
        else _default_worktree_path(repo_root, selected_branch)
    )
    selected_worktree_path.parent.mkdir(parents=True, exist_ok=True)

    _run_git(["fetch", remote, base], cwd=repo_root, check=True)
    base_ref = f"{remote}/{base}"
    _run_git(
        ["worktree", "add", "-b", selected_branch, str(selected_worktree_path), base_ref],
        cwd=repo_root,
        check=True,
    )

    metadata: dict[str, Any] = {
        "schema_version": "1.0",
        "branch": selected_branch,
        "base_branch": base,
        "remote": remote,
        "repo_root": str(repo_root),
        "worktree_path": str(selected_worktree_path),
        "run_dir": str(run_dir),
        "dirty_policy": dirty_policy,
        "timestamp_utc": _timestamp_utc(),
    }
    (run_dir / "WORKTREE.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return metadata


def commit_sequence(
    *,
    run_dir: Path,
    allow_unpromoted: bool,
    dirty_policy: str,
    cwd: Path | None = None,
) -> dict[str, Any]:
    """Execute COMMIT PLAN step-by-step with allowlist-only staging."""
    invoke_cwd = (cwd or Path.cwd()).resolve()
    repo_root = _git_repo_root(invoke_cwd)
    run_dir = run_dir.resolve()
    run_dir.mkdir(parents=True, exist_ok=True)

    branch = _git_current_branch(repo_root)
    if branch == "main":
        raise RuntimeError(
            "ERROR: commit-sequence cannot run on 'main'.\n"
            "Use dopetask wt start to create a worktree."
        )

    preflight_status = _git_status_porcelain(repo_root)
    if _has_staged_changes(preflight_status):
        raise RuntimeError(
            "ERROR: git index already contains staged files.\n"
            "Commit-sequence requires a clean index."
        )

    if not allow_unpromoted:
        promoted = (run_dir / "PROMOTION_TOKEN.json").exists() or (run_dir / "PROMOTION.json").exists()
        if not promoted:
            raise RuntimeError(
                "Run is not promoted (missing PROMOTION_TOKEN.json/PROMOTION.json).\n"
                "Use --allow-unpromoted to bypass."
            )

    task_packet = run_dir / "TASK_PACKET.md"
    steps = _load_commit_plan(task_packet)
    union_allowlist = {path for step in steps for path in step.allowlist}
    changed_paths = _status_paths(preflight_status)
    disallowed_changes = sorted(changed_paths - union_allowlist)

    if disallowed_changes:
        if dirty_policy == "refuse":
            raise RuntimeError(
                "ERROR: changes detected outside commit plan allowlists.\n"
                "Use --dirty-policy stash or clean manually."
            )

        stash_message = f"dopetask:commit-sequence:{run_dir.name}"
        stash_ref = _stash_changes(
            repo_root=repo_root,
            message=stash_message,
            include_ignored=False,
            paths=disallowed_changes,
        )
        _append_dirty_state(
            run_dir=run_dir,
            location="worktree",
            policy="stash",
            stash_ref=stash_ref,
            message=stash_message,
            status_porcelain=preflight_status,
        )

    report: dict[str, Any] = {
        "schema_version": "1.0",
        "branch": branch,
        "run_dir": str(run_dir),
        "repo_root": str(repo_root),
        "dirty_policy": dirty_policy,
        "allow_unpromoted": allow_unpromoted,
        "steps": [],
        "timestamp_utc": _timestamp_utc(),
    }

    for step in steps:
        verify_results = _run_verify_commands(repo_root, step.verify)
        status_lines = _git_status_porcelain(repo_root)
        status_paths = _status_paths(status_lines)
        stage_paths = sorted(status_paths.intersection(set(step.allowlist)))
        if not stage_paths:
            raise RuntimeError(
                f"ERROR: step {step.step_id} would create an empty commit.\n"
                "No allowlisted changed files found."
            )

        _run_git(["add", "--", *stage_paths], cwd=repo_root, check=True)
        _run_git(["commit", "-m", step.message], cwd=repo_root, check=True)
        commit_sha = _git_output(["rev-parse", "HEAD"], cwd=repo_root)

        report["steps"].append(
            {
                "step_id": step.step_id,
                "message": step.message,
                "allowlist": step.allowlist,
                "staged_files": stage_paths,
                "verify": verify_results,
                "commit": commit_sha,
            }
        )

    (run_dir / "COMMIT_SEQUENCE_RUN.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def _load_worktree_metadata(run_dir: Path) -> dict[str, Any]:
    """Load optional WORKTREE.json metadata for defaults."""
    worktree_json = run_dir / "WORKTREE.json"
    if not worktree_json.exists():
        return {}
    try:
        payload = json.loads(worktree_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _find_worktree_for_branch(repo_root: Path, branch: str) -> Path | None:
    """Find worktree path where branch is currently checked out."""
    proc = _run_git(["worktree", "list", "--porcelain"], cwd=repo_root, check=True)
    blocks = proc.stdout.split("\n\n")
    branch_ref = f"refs/heads/{branch}"
    for block in blocks:
        worktree_path: Path | None = None
        branch_line = ""
        for line in block.splitlines():
            if line.startswith("worktree "):
                worktree_path = Path(line.removeprefix("worktree ").strip())
            elif line.startswith("branch "):
                branch_line = line.removeprefix("branch ").strip()
        if worktree_path is not None and branch_line == branch_ref:
            return worktree_path
    return None


def finish_run(
    *,
    run_dir: Path,
    mode: str,
    cleanup: bool,
    dirty_policy: str,
    cwd: Path | None = None,
) -> dict[str, Any]:
    """Finalize task branch into main using rebase + ff + push."""
    if mode != "rebase-ff":
        raise RuntimeError("Only mode 'rebase-ff' is supported")

    invoke_cwd = (cwd or Path.cwd()).resolve()
    repo_root = _git_repo_root(invoke_cwd)
    run_dir = run_dir.resolve()
    run_dir.mkdir(parents=True, exist_ok=True)

    meta = _load_worktree_metadata(run_dir)
    branch = str(meta.get("branch") or _git_current_branch(repo_root))
    base_branch = str(meta.get("base_branch") or "main")
    remote = str(meta.get("remote") or "origin")

    _ensure_not_dirty_or_stash_all(
        repo_root=repo_root,
        run_dir=run_dir,
        dirty_policy=dirty_policy,
        stash_message=f"dopetask:finish:{run_dir.name}",
        location="worktree",
    )

    _run_git(["fetch", remote, base_branch], cwd=repo_root, check=True)

    pre_rebase_head = _git_output(["rev-parse", "HEAD"], cwd=repo_root)
    rebase = _run_git(["rebase", f"{remote}/{base_branch}"], cwd=repo_root, check=False)
    if rebase.returncode != 0:
        _run_git(["rebase", "--abort"], cwd=repo_root, check=False)
        raise RuntimeError(
            "ERROR: rebase onto origin/main failed.\n"
            "Resolve conflicts manually and re-run dopetask finish."
        )
    post_rebase_head = _git_output(["rev-parse", "HEAD"], cwd=repo_root)

    merge_worktree = _find_worktree_for_branch(repo_root, base_branch)
    temp_worktree_created = False
    temp_worktree_path = run_dir / ".dopetask_finish_main"
    if merge_worktree is None:
        temp_worktree_path.mkdir(parents=True, exist_ok=True)
        _run_git(
            ["worktree", "add", str(temp_worktree_path), base_branch],
            cwd=repo_root,
            check=True,
        )
        merge_worktree = temp_worktree_path
        temp_worktree_created = True

    sync_main = _run_git(["merge", "--ff-only", f"{remote}/{base_branch}"], cwd=merge_worktree, check=False)
    if sync_main.returncode != 0:
        if temp_worktree_created:
            _run_git(["worktree", "remove", "--force", str(temp_worktree_path)], cwd=repo_root, check=False)
        raise RuntimeError(
            "ERROR: main is not fast-forwardable.\n"
            "Repository state diverged."
        )

    main_before_merge = _git_output(["rev-parse", base_branch], cwd=merge_worktree)
    merge_result = _run_git(["merge", "--ff-only", branch], cwd=merge_worktree, check=False)
    if merge_result.returncode != 0:
        if temp_worktree_created:
            _run_git(["worktree", "remove", "--force", str(temp_worktree_path)], cwd=repo_root, check=False)
        raise RuntimeError(
            "ERROR: main is not fast-forwardable.\n"
            "Repository state diverged."
        )
    main_after_merge = _git_output(["rev-parse", base_branch], cwd=merge_worktree)

    push_result = _run_git(["push", remote, base_branch], cwd=merge_worktree, check=False)
    if push_result.returncode != 0:
        if temp_worktree_created:
            _run_git(["worktree", "remove", "--force", str(temp_worktree_path)], cwd=repo_root, check=False)
        raise RuntimeError(
            "ERROR: push to origin/main failed.\n"
            "Local and remote are not synchronized."
        )

    _run_git(["fetch", remote, base_branch], cwd=merge_worktree, check=True)
    remote_after_push = _git_output(["rev-parse", f"{remote}/{base_branch}"], cwd=merge_worktree)
    if main_after_merge != remote_after_push:
        if temp_worktree_created:
            _run_git(["worktree", "remove", "--force", str(temp_worktree_path)], cwd=repo_root, check=False)
        raise RuntimeError(
            "ERROR: push to origin/main failed.\n"
            "Local and remote are not synchronized."
        )

    cleanup_warnings: list[str] = []
    if cleanup:
        worktree_path = meta.get("worktree_path")
        if isinstance(worktree_path, str) and worktree_path.strip():
            remove_result = _run_git(
                ["worktree", "remove", "--force", worktree_path],
                cwd=merge_worktree,
                check=False,
            )
            if remove_result.returncode != 0:
                warning = (remove_result.stderr or remove_result.stdout).strip()
                cleanup_warnings.append(f"worktree remove failed: {warning}")
        if branch != base_branch:
            delete_result = _run_git(["branch", "-D", branch], cwd=merge_worktree, check=False)
            if delete_result.returncode != 0:
                warning = (delete_result.stderr or delete_result.stdout).strip()
                cleanup_warnings.append(f"branch delete failed: {warning}")

    if temp_worktree_created:
        _run_git(["worktree", "remove", "--force", str(temp_worktree_path)], cwd=repo_root, check=False)

    report: dict[str, Any] = {
        "schema_version": "1.0",
        "mode": mode,
        "branch": branch,
        "base_branch": base_branch,
        "remote": remote,
        "pre_rebase_head": pre_rebase_head,
        "post_rebase_head": post_rebase_head,
        "main_before_merge": main_before_merge,
        "main_after_merge": main_after_merge,
        "remote_after_push": remote_after_push,
        "cleanup": cleanup,
        "dirty_policy": dirty_policy,
        "timestamp_utc": _timestamp_utc(),
    }
    if cleanup_warnings:
        report["cleanup_warnings"] = cleanup_warnings

    (run_dir / "FINISH.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report
