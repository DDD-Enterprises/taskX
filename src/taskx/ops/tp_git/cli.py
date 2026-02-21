"""CLI surface for taskx tp git workflows."""

from __future__ import annotations

from pathlib import Path

import typer

from taskx.ops.tp_git.guards import run_doctor
from taskx.ops.tp_git.git_worktree import cleanup_tp, list_worktrees, start_tp, sync_main
from taskx.ops.tp_git.github import merge_pr, pr_create, pr_status

app = typer.Typer(
    name="git",
    help="Task Packet git workflow commands",
    no_args_is_help=True,
)


@app.command("doctor")
def doctor(
    repo: Path | None = typer.Option(
        None,
        "--repo",
        help="Repository path (defaults to current working directory).",
    ),
) -> None:
    """Fail-closed gate: clean main, no stashes, and fast-forward sync."""
    try:
        report = run_doctor(repo=repo)
    except RuntimeError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc

    typer.echo(f"repo_root={report.repo_root}")
    typer.echo(f"branch={report.branch}")
    typer.echo("status_porcelain=clean")
    typer.echo("stash_list=empty")
    typer.echo(f"worktree_base={(report.repo_root / '.worktrees').resolve()}")
    fetch_out = report.fetch.stdout.strip() or report.fetch.stderr.strip() or "(no output)"
    pull_out = report.pull.stdout.strip() or report.pull.stderr.strip() or "(no output)"
    typer.echo(f"fetch={fetch_out}")
    typer.echo(f"pull={pull_out}")


@app.command("start")
def start(
    tp_id: str = typer.Argument(..., metavar="TP_ID"),
    slug: str = typer.Argument(...),
    repo: Path | None = typer.Option(
        None,
        "--repo",
        help="Repository path (defaults to current working directory).",
    ),
    reuse: bool = typer.Option(
        False,
        "--reuse",
        help="Reuse existing TP worktree only when branch and clean state match.",
    ),
) -> None:
    """Create deterministic TP branch + worktree from clean main."""
    try:
        result = start_tp(tp_id=tp_id, slug=slug, repo=repo, reuse=reuse)
    except RuntimeError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc

    typer.echo(f"repo_root={result.doctor.repo_root}")
    typer.echo(f"tp_id={tp_id}")
    typer.echo(f"branch={result.branch}")
    typer.echo(f"worktree_path={result.worktree_path}")
    typer.echo(f"reused={str(result.reused).lower()}")
    typer.echo(f"next=cd {result.worktree_path}")


@app.command("status")
def status(
    tp_id: str = typer.Argument(..., metavar="TP_ID"),
    repo: Path | None = typer.Option(
        None,
        "--repo",
        help="Repository path (defaults to current working directory).",
    ),
) -> None:
    """Show TP local state and PR metadata when available."""
    try:
        payload = pr_status(tp_id=tp_id, repo=repo)
    except RuntimeError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc

    typer.echo(f"repo_root={payload['repo_root']}")
    typer.echo(f"tp_id={payload['tp_id']}")
    typer.echo(f"worktree_path={payload['worktree_path']}")
    typer.echo(f"branch={payload['branch']}")
    typer.echo(f"dirty={'yes' if payload['dirty'] else 'no'}")
    pr_payload = payload.get("pr")
    if isinstance(pr_payload, dict):
        typer.echo(f"pr_url={pr_payload.get('url', '')}")
        typer.echo(f"pr_state={pr_payload.get('state', '')}")
    elif "pr_error" in payload:
        typer.echo(f"pr_error={payload['pr_error']}")


@app.command("pr")
def pr(
    tp_id: str = typer.Argument(..., metavar="TP_ID"),
    title: str = typer.Option(..., "--title", help="Pull request title."),
    body: str | None = typer.Option(None, "--body", help="Pull request body text."),
    body_file: Path | None = typer.Option(None, "--body-file", help="Pull request body file path."),
    repo: Path | None = typer.Option(
        None,
        "--repo",
        help="Repository path (defaults to current working directory).",
    ),
) -> None:
    """Push TP branch and open PR via GitHub CLI."""
    if body is not None and body_file is not None:
        typer.echo("pr failed: pass either --body or --body-file, not both", err=True)
        raise typer.Exit(1)

    try:
        payload = pr_create(tp_id=tp_id, title=title, body=body, body_file=body_file, repo=repo)
    except RuntimeError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc

    typer.echo(f"repo_root={payload['repo_root']}")
    typer.echo(f"tp_id={payload['tp_id']}")
    typer.echo(f"branch={payload['branch']}")
    typer.echo(f"worktree_path={payload['worktree_path']}")
    typer.echo(f"url={payload.get('url', '')}")
    typer.echo(f"state={payload.get('state', '')}")
    typer.echo(f"mergeStateStatus={payload.get('mergeStateStatus', '')}")


@app.command("merge")
def merge(
    tp_id: str = typer.Argument(..., metavar="TP_ID"),
    squash: bool = typer.Option(False, "--squash", help="Use squash merge mode."),
    merge_flag: bool = typer.Option(False, "--merge", help="Use merge commit mode."),
    rebase: bool = typer.Option(False, "--rebase", help="Use rebase merge mode."),
    repo: Path | None = typer.Option(
        None,
        "--repo",
        help="Repository path (defaults to current working directory).",
    ),
) -> None:
    """Attempt auto-merge for TP PR via GitHub CLI."""
    selected = [name for enabled, name in ((squash, "squash"), (merge_flag, "merge"), (rebase, "rebase")) if enabled]
    if len(selected) > 1:
        typer.echo("merge failed: choose only one mode flag", err=True)
        raise typer.Exit(1)
    mode = selected[0] if selected else "squash"

    try:
        payload = merge_pr(tp_id=tp_id, mode=mode, repo=repo)
    except RuntimeError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc

    typer.echo(f"repo_root={payload['repo_root']}")
    typer.echo(f"tp_id={payload['tp_id']}")
    typer.echo(f"mode={payload['mode']}")
    typer.echo(f"url={payload.get('url', '')}")
    typer.echo(f"state={payload.get('state', '')}")
    typer.echo(f"mergeStateStatus={payload.get('mergeStateStatus', '')}")


@app.command("sync-main")
def sync_main_cmd(
    repo: Path | None = typer.Option(
        None,
        "--repo",
        help="Repository path (defaults to current working directory).",
    ),
) -> None:
    """Checkout main and fast-forward sync from origin."""
    try:
        payload = sync_main(repo=repo)
    except RuntimeError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc

    typer.echo(f"repo_root={payload['repo_root']}")
    typer.echo(f"fetch={payload['fetch']}")
    typer.echo(f"pull={payload['pull']}")


@app.command("cleanup")
def cleanup(
    tp_id: str = typer.Argument(..., metavar="TP_ID"),
    repo: Path | None = typer.Option(
        None,
        "--repo",
        help="Repository path (defaults to current working directory).",
    ),
) -> None:
    """Remove TP worktree and prune stale worktree metadata."""
    try:
        payload = cleanup_tp(tp_id=tp_id, repo=repo)
    except RuntimeError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc

    typer.echo(f"repo_root={payload['repo_root']}")
    typer.echo(f"tp_id={tp_id}")
    typer.echo(f"worktree_path={payload['worktree_path']}")
    typer.echo(f"remove={payload['remove']}")
    typer.echo(f"prune={payload['prune']}")


@app.command("list")
def list_cmd(
    repo: Path | None = typer.Option(
        None,
        "--repo",
        help="Repository path (defaults to current working directory).",
    ),
) -> None:
    """List worktrees and highlight TaskX TP worktree paths."""
    try:
        listing = list_worktrees(repo=repo)
    except RuntimeError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc

    for raw_line in listing.splitlines():
        marker = "[tp]" if "/.worktrees/" in raw_line else "     "
        typer.echo(f"{marker} {raw_line}")
