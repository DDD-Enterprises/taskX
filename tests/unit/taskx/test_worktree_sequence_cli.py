"""CLI tests for worktree + commit sequencing command refusals."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from typer.testing import CliRunner

from taskx.cli import cli

if TYPE_CHECKING:
    from pathlib import Path


def _init_repo(path: Path) -> None:
    """Create a minimal git repo with one commit on main."""
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-b", "main"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=path, check=True, capture_output=True)
    (path / "README.md").write_text("# repo\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=path, check=True, capture_output=True)


def _write_task_packet_with_commit_plan(run_dir: Path) -> None:
    """Write minimal packet with COMMIT PLAN section."""
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "TASK_PACKET.md").write_text(
        """# TASK_PACKET TP_0001 — Sample

## COMMIT PLAN
```json
{
  "commit_plan": [
    {
      "step_id": "C1",
      "message": "sample commit",
      "allowlist": ["src/file.py"],
      "verify": []
    }
  ]
}
```
""",
        encoding="utf-8",
    )


def test_wt_start_refuses_dirty_repo(tmp_path: Path, monkeypatch) -> None:
    """`taskx wt start` should hard-refuse dirty repo by default."""
    repo = tmp_path / "repo"
    _init_repo(repo)
    (repo / "dirty.txt").write_text("dirty\n", encoding="utf-8")

    runner = CliRunner()
    run_dir = repo / "out" / "runs" / "RUN_0123"
    monkeypatch.chdir(repo)
    result = runner.invoke(cli, ["wt", "start", "--run", str(run_dir)])

    assert result.exit_code == 1
    assert "ERROR: repository working tree is dirty." in result.stdout
    assert "Run with --dirty-policy stash to stash changes, or clean manually." in result.stdout


def test_wt_start_refuses_existing_branch(tmp_path: Path, monkeypatch) -> None:
    """`taskx wt start` should refuse branch reuse for deterministic execution."""
    repo = tmp_path / "repo"
    _init_repo(repo)
    subprocess.run(["git", "branch", "tp/0123-feature"], cwd=repo, check=True, capture_output=True)

    runner = CliRunner()
    run_dir = repo / "out" / "runs" / "RUN_0123"
    monkeypatch.chdir(repo)
    result = runner.invoke(
        cli,
        [
            "wt",
            "start",
            "--run",
            str(run_dir),
            "--branch",
            "tp/0123-feature",
        ],
    )

    assert result.exit_code == 1
    assert "ERROR: branch 'tp/0123-feature' already exists." in result.stdout
    assert "Refusing to reuse branch for deterministic execution." in result.stdout


def test_commit_sequence_refuses_on_main(tmp_path: Path, monkeypatch) -> None:
    """`taskx commit-sequence` should refuse execution on main."""
    repo = tmp_path / "repo"
    _init_repo(repo)
    run_dir = repo / "out" / "runs" / "RUN_0123"
    _write_task_packet_with_commit_plan(run_dir)

    runner = CliRunner()
    monkeypatch.chdir(repo)
    result = runner.invoke(
        cli,
        [
            "commit-sequence",
            "--run",
            str(run_dir),
            "--allow-unpromoted",
        ],
    )

    assert result.exit_code == 1
    assert "ERROR: commit-sequence cannot run on 'main'." in result.stdout
    assert "Use taskx wt start to create a worktree." in result.stdout


def test_commit_sequence_refuses_with_staged_files(tmp_path: Path, monkeypatch) -> None:
    """`taskx commit-sequence` should refuse when index is pre-staged."""
    repo = tmp_path / "repo"
    _init_repo(repo)
    subprocess.run(["git", "checkout", "-b", "tp/test"], cwd=repo, check=True, capture_output=True)

    src_dir = repo / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "file.py").write_text("print('x')\n", encoding="utf-8")
    subprocess.run(["git", "add", "src/file.py"], cwd=repo, check=True, capture_output=True)

    run_dir = repo / "out" / "runs" / "RUN_0123"
    _write_task_packet_with_commit_plan(run_dir)

    runner = CliRunner()
    monkeypatch.chdir(repo)
    result = runner.invoke(
        cli,
        [
            "commit-sequence",
            "--run",
            str(run_dir),
            "--allow-unpromoted",
        ],
    )

    assert result.exit_code == 1
    assert "ERROR: git index already contains staged files." in result.stdout
    assert "Commit-sequence requires a clean index." in result.stdout


def test_commit_sequence_refuses_empty_step(tmp_path: Path, monkeypatch) -> None:
    """`taskx commit-sequence` should refuse empty commits per step."""
    repo = tmp_path / "repo"
    _init_repo(repo)
    subprocess.run(["git", "checkout", "-b", "tp/test"], cwd=repo, check=True, capture_output=True)
    run_dir = tmp_path / "RUN_0123"
    _write_task_packet_with_commit_plan(run_dir)

    runner = CliRunner()
    monkeypatch.chdir(repo)
    result = runner.invoke(
        cli,
        [
            "commit-sequence",
            "--run",
            str(run_dir),
            "--allow-unpromoted",
        ],
    )

    assert result.exit_code == 1
    assert "ERROR: step C1 would create an empty commit." in result.stdout
    assert "No allowlisted changed files found." in result.stdout


def test_commit_sequence_accepts_unstaged_allowlisted_changes(tmp_path: Path, monkeypatch) -> None:
    """Unstaged allowlisted edits should be committed by commit-sequence."""
    repo = tmp_path / "repo"
    _init_repo(repo)
    subprocess.run(["git", "checkout", "-b", "tp/test"], cwd=repo, check=True, capture_output=True)

    src_dir = repo / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    tracked = src_dir / "file.py"
    tracked.write_text("print('a')\n", encoding="utf-8")
    subprocess.run(["git", "add", "src/file.py"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "add tracked file"], cwd=repo, check=True, capture_output=True)

    tracked.write_text("print('b')\n", encoding="utf-8")

    run_dir = tmp_path / "RUN_0123"
    _write_task_packet_with_commit_plan(run_dir)

    runner = CliRunner()
    monkeypatch.chdir(repo)
    result = runner.invoke(
        cli,
        [
            "commit-sequence",
            "--run",
            str(run_dir),
            "--allow-unpromoted",
        ],
    )

    assert result.exit_code == 0
    assert "✓ Commit sequence complete" in result.stdout
    assert (run_dir / "COMMIT_SEQUENCE_RUN.json").exists()
