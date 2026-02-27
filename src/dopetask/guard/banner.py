"""Identity banner helpers for dopeTask commands."""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING

from dopetask.guard.identity import origin_hint_warning

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True)
class BannerContext:
    """One-line identity banner context."""

    project_id: str
    project_slug: str | None
    branch: str | None
    run_id: str | None
    origin_url: str | None
    repo_remote_hint: str | None


def _use_color() -> bool:
    if not sys.stderr.isatty():
        return False
    return os.getenv("NO_COLOR") is None


def _c(text: str, code: str) -> str:
    if not _use_color():
        return text
    return f"\033[{code}m{text}\033[0m"


def _git(repo_root: Path, *args: str) -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "-C", str(repo_root), *args],
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return None
    return out.decode("utf-8", errors="replace").strip() or None


def get_banner_context(
    repo_root: Path,
    project_id: str,
    project_slug: str | None,
    repo_remote_hint: str | None,
    run_dir: Path | None,
) -> BannerContext:
    """Gather context for command identity banner."""
    branch = _git(repo_root, "rev-parse", "--abbrev-ref", "HEAD")
    origin_url = _git(repo_root, "remote", "get-url", "origin")
    run_id = run_dir.name if run_dir is not None else None
    return BannerContext(
        project_id=project_id,
        project_slug=project_slug,
        branch=branch,
        run_id=run_id,
        origin_url=origin_url,
        repo_remote_hint=repo_remote_hint,
    )


def print_identity_banner(ctx: BannerContext, *, quiet: bool = False) -> None:
    """Print one-line identity banner and optional warning to stderr."""
    if quiet:
        return

    repo = ctx.project_slug or ctx.project_id
    branch = ctx.branch or "UNKNOWN"
    run = ctx.run_id or "none"

    banner = f"[dopetask] project={ctx.project_id} repo={repo} branch={branch} run={run}"
    print(_c(banner, "36"), file=sys.stderr)

    warning = origin_hint_warning(ctx.repo_remote_hint, ctx.origin_url)
    if warning is not None:
        print(_c(warning, "33"), file=sys.stderr)
