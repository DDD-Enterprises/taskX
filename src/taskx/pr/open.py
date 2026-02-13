"""Assisted pull request open flow with restore rails."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from taskx.git.branch_guard import (
    GitState,
    PreflightFlags,
    PreflightRefusal,
    preflight_or_refuse,
    restore_git_state,
)

REPORT_DIR = Path("out/taskx_pr")
REPORT_JSON = "PR_OPEN_REPORT.json"
REPORT_MD = "PR_OPEN_REPORT.md"


class PrOpenRefusal(RuntimeError):
    """Raised when PR open flow must refuse with exit code 2."""


def run_pr_open(
    *,
    repo_root: Path,
    title: str,
    body_file: Path,
    base: str,
    remote: str,
    draft: bool,
    restore_branch: bool,
    allow_dirty: bool,
    allow_detached: bool,
    allow_base_branch: bool,
) -> dict[str, Any]:
    """Execute assisted PR open flow with deterministic report artifacts."""
    resolved_repo = repo_root.resolve()
    resolved_body = body_file.resolve()

    if not resolved_body.exists():
        raise RuntimeError(f"Body file not found: {resolved_body}")

    state: GitState | None = None
    report: dict[str, Any] = {
        "status": "failed",
        "repo_root": str(resolved_repo),
        "title": title,
        "body_file": str(resolved_body),
        "base": base,
        "remote": remote,
        "draft": draft,
        "restore_branch": restore_branch,
        "allow_dirty": allow_dirty,
        "allow_detached": allow_detached,
        "allow_base_branch": allow_base_branch,
        "push_command": "",
        "pr_command": "",
        "pr_url": None,
        "fallback_url": None,
        "refusal_reason": None,
        "error": None,
        "captured_state": None,
        "restored_state": False,
        "branch_used": None,
        "head_sha": None,
    }

    try:
        state = preflight_or_refuse(
            resolved_repo,
            PreflightFlags(
                allow_dirty=allow_dirty,
                allow_detached=allow_detached,
                allow_base_branch=allow_base_branch,
                base_branch=base,
            ),
        )
        report["captured_state"] = {
            "mode": state.mode,
            "branch": state.branch,
            "head_sha": state.head_sha,
        }
        report["head_sha"] = state.head_sha

        branch = state.branch
        if state.mode == "detached":
            branch = _branch_for_detached(resolved_repo, state.head_sha)
            if not branch:
                raise PrOpenRefusal(
                    "Refused: cannot determine branch for detached HEAD; use --allow-detached with branch checkout."
                )

        report["branch_used"] = branch
        assert branch is not None

        push_cmd = _build_push_command(resolved_repo, remote=remote, branch=branch)
        report["push_command"] = " ".join(push_cmd)
        _run(push_cmd, cwd=resolved_repo)

        gh_path = shutil.which("gh")
        if gh_path:
            pr_cmd = [
                gh_path,
                "pr",
                "create",
                "--title",
                title,
                "--body-file",
                str(resolved_body),
                "--base",
                base,
                "--head",
                branch,
            ]
            if draft:
                pr_cmd.append("--draft")
            report["pr_command"] = " ".join(pr_cmd)
            created = _run(pr_cmd, cwd=resolved_repo)
            report["pr_url"] = _extract_pr_url(created.stdout)
            if report["pr_url"] is None:
                raise RuntimeError("gh pr create succeeded but did not return a PR URL")
        else:
            remote_url = _git_output(resolved_repo, ["remote", "get-url", remote])
            owner_repo = _parse_owner_repo(remote_url)
            if owner_repo is None:
                raise PrOpenRefusal(f"Refused: cannot derive owner/repo from remote URL `{remote_url}`")
            fallback_url = f"https://github.com/{owner_repo}/pull/new/{branch}"
            report["fallback_url"] = fallback_url
            report["pr_url"] = fallback_url
            report["pr_command"] = "fallback-url"

        report["status"] = "ok"
    except PreflightRefusal as exc:
        report["status"] = "refused"
        report["refusal_reason"] = str(exc)
        raise PrOpenRefusal(str(exc)) from exc
    except PrOpenRefusal as exc:
        report["status"] = "refused"
        report["refusal_reason"] = str(exc)
        raise
    except Exception as exc:
        report["status"] = "failed"
        report["error"] = str(exc)
        raise
    finally:
        if restore_branch and state is not None:
            restore_git_state(resolved_repo, state)
            report["restored_state"] = True

        _write_reports(resolved_repo, report)

    return report


def _run(cmd: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(cmd, cwd=cwd, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        stderr = (completed.stderr or completed.stdout).strip()
        raise RuntimeError(f"command failed ({' '.join(cmd)}): {stderr}")
    return completed


def _git_output(repo_root: Path, args: list[str]) -> str:
    return _run(["git", *args], cwd=repo_root).stdout.strip()


def _build_push_command(repo_root: Path, *, remote: str, branch: str) -> list[str]:
    upstream = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if upstream.returncode == 0:
        return ["git", "push", remote, branch]
    return ["git", "push", "-u", remote, branch]


def _parse_owner_repo(remote_url: str) -> str | None:
    ssh_match = re.match(r"^git@github\.com:(?P<owner>[^/]+)/(?P<repo>[^/.]+)(?:\.git)?$", remote_url)
    if ssh_match:
        return f"{ssh_match.group('owner')}/{ssh_match.group('repo')}"

    https_match = re.match(
        r"^https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/.]+)(?:\.git)?/?$",
        remote_url,
    )
    if https_match:
        return f"{https_match.group('owner')}/{https_match.group('repo')}"

    return None


def _extract_pr_url(stdout_text: str) -> str | None:
    for line in stdout_text.splitlines():
        value = line.strip()
        if value.startswith("http://") or value.startswith("https://"):
            return value
    return None


def _branch_for_detached(repo_root: Path, head_sha: str) -> str | None:
    refs = _git_output(repo_root, ["for-each-ref", "--format=%(refname:short) %(objectname)", "refs/heads"])
    candidates: list[str] = []
    for line in refs.splitlines():
        if not line.strip():
            continue
        branch, sha = line.split(" ", 1)
        if sha.strip() == head_sha:
            candidates.append(branch.strip())
    if not candidates:
        return None
    return sorted(candidates)[0]


def _write_reports(repo_root: Path, report: dict[str, Any]) -> None:
    out_dir = repo_root / REPORT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / REPORT_JSON
    md_path = out_dir / REPORT_MD

    json_path.write_text(json.dumps(report, sort_keys=True, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown_report(report), encoding="utf-8")


def _render_markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# PR_OPEN_REPORT",
        "",
        f"- status: {report['status']}",
        f"- repo_root: {report['repo_root']}",
        f"- remote: {report['remote']}",
        f"- base: {report['base']}",
        f"- branch_used: {report['branch_used']}",
        f"- restore_branch: {report['restore_branch']}",
        f"- restored_state: {report['restored_state']}",
        f"- pr_url: {report['pr_url']}",
        "",
        "## Commands",
        "",
        f"- push_command: {report['push_command']}",
        f"- pr_command: {report['pr_command']}",
    ]

    if report.get("refusal_reason"):
        lines.extend(["", "## Refusal", "", f"- {report['refusal_reason']}"])

    if report.get("error"):
        lines.extend(["", "## Error", "", f"- {report['error']}"])

    lines.append("")
    return "\n".join(lines)
