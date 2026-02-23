"""Tests for Task Packet project identity guard behavior."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

import pytest
from typer.testing import CliRunner

from dopetask.cli import cli
from dopetask.guard.identity import RepoIdentity, assert_repo_packet_identity
from dopetask.pipeline.task_runner.parser import parse_packet_project_identity
from dopetask.pipeline.task_runner.types import ProjectIdentity

if TYPE_CHECKING:
    from pathlib import Path


def test_packet_project_id_mismatch_refuses_with_exact_message() -> None:
    """Mismatched task packet project_id should hard-fail with exact refusal text."""
    repo_identity = RepoIdentity(
        project_id="taskx",
        project_slug="taskX",
        repo_remote_hint="taskX",
        packet_required_header=True,
    )
    packet_identity = ProjectIdentity(project_id="adops", intended_repo="adops")

    with pytest.raises(RuntimeError) as exc_info:
        assert_repo_packet_identity(repo_identity, packet_identity)

    assert str(exc_info.value) == (
        "ERROR: Task Packet project_id 'adops' does not match repo project_id 'taskx'.\n"
        "Refusing to run. Use the correct repo or correct packet."
    )


def test_missing_project_identity_header_refuses_when_required(tmp_path: Path) -> None:
    """Missing PROJECT IDENTITY section should fail when header is required."""
    packet = tmp_path / "TASK_PACKET.md"
    packet.write_text(
        "# TASK_PACKET TP_0001 — Demo\n\n"
        "## GOAL\n"
        "A small packet.\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError) as exc_info:
        parse_packet_project_identity(packet, packet_required_header=True)

    assert str(exc_info.value) == (
        "ERROR: Task Packet missing required PROJECT IDENTITY header.\n"
        "Refusing to run."
    )


def test_wt_start_refuses_packet_repo_mismatch_with_exact_message(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """wt start should stop before worktree operations on packet/repo mismatch."""
    repo = tmp_path / "repo"
    repo.mkdir(parents=True, exist_ok=True)

    subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True, capture_output=True)
    (repo / "README.md").write_text("# repo\n", encoding="utf-8")
    (repo / ".gitignore").write_text("out/\n", encoding="utf-8")
    (repo / ".taskxroot").write_text("", encoding="utf-8")
    (repo / ".taskx").mkdir(parents=True, exist_ok=True)
    (repo / ".taskx" / "project.json").write_text(
        "{\n"
        '  "project_id": "taskx",\n'
        '  "project_slug": "taskX",\n'
        '  "repo_remote_hint": "taskX",\n'
        '  "packet_required_header": true\n'
        "}\n",
        encoding="utf-8",
    )
    subprocess.run(
        ["git", "add", "README.md", ".gitignore", ".taskxroot", ".taskx/project.json"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True, capture_output=True)

    run_dir = repo / "out" / "runs" / "RUN_X"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "TASK_PACKET.md").write_text(
        "# TASK_PACKET TP_0001 — Wrong Project\n\n"
        "## PROJECT IDENTITY\n"
        "project_id: adops\n"
        "intended_repo: adops\n",
        encoding="utf-8",
    )

    runner = CliRunner()
    monkeypatch.chdir(repo)
    result = runner.invoke(cli, ["wt", "start", "--run", str(run_dir), "--dirty-policy", "refuse"])

    assert result.exit_code == 1
    assert (
        "ERROR: Task Packet project_id 'adops' does not match repo project_id 'taskx'.\n"
        "Refusing to run. Use the correct repo or correct packet."
    ) in result.stdout
