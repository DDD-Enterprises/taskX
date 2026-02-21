"""CLI registration for taskx tp run commands."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import typer

from taskx.ops.tp_git.guards import resolve_repo_root
from taskx.ops.tp_git.naming import normalize_slug
from taskx.ops.tp_run.proof import ProofWriter, build_run_id, resolve_paths


def register(tp_app: typer.Typer) -> None:
    """Attach tp run command to the tp group."""

    @tp_app.command("run")
    def tp_run(
        tp_id: str = typer.Argument(..., metavar="TP_ID"),
        slug: str = typer.Argument(...),
        repo: Path | None = typer.Option(None, "--repo", help="Repository path."),
        dry_run: bool = typer.Option(False, "--dry-run", help="Generate proof pack without mutating git state."),
    ) -> None:
        """Run complete TP lifecycle (scaffold; writes deterministic proof pack)."""
        try:
            repo_root = resolve_repo_root(repo)
        except RuntimeError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(1) from exc

        normalized_slug = normalize_slug(slug)
        run_id = build_run_id(tp_id=tp_id, repo_root=repo_root)
        paths = resolve_paths(repo_root=repo_root, tp_id=tp_id, run_id=run_id)
        writer = ProofWriter(paths)

        started_at = datetime.now(UTC).isoformat()
        writer.write_json(
            "RUN.json",
            {
                "tp_id": tp_id,
                "slug": normalized_slug,
                "run_id": run_id,
                "repo_root": str(repo_root),
                "proof_dir": str(paths.run_dir),
                "dry_run": dry_run,
                "start_time": started_at,
                "end_time": datetime.now(UTC).isoformat(),
            },
        )

        typer.echo(f"repo_root={repo_root}")
        typer.echo(f"tp_id={tp_id}")
        typer.echo(f"slug={normalized_slug}")
        typer.echo(f"run_id={run_id}")
        typer.echo(f"proof_dir={paths.run_dir}")
        if dry_run:
            typer.echo("mode=dry-run")
