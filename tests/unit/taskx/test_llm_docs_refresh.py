"""Tests for marker-scoped LLM docs refresh."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from typer.testing import CliRunner

from taskx.cli import cli
from taskx.docs.llm_refresh import (
    AUTOGEN_END,
    AUTOGEN_START,
    ensure_autogen_markers,
    replace_autogen_block,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_ensure_autogen_markers_inserts_block_when_missing(tmp_path: Path) -> None:
    """Marker block should be appended when missing."""
    path = tmp_path / "CLAUDE.md"
    path.write_text("# Title\n\nStatic content.\n", encoding="utf-8")

    ensure_autogen_markers(path)

    text = path.read_text(encoding="utf-8")
    assert AUTOGEN_START in text
    assert AUTOGEN_END in text


def test_replace_autogen_block_preserves_outside_content_exactly(tmp_path: Path) -> None:
    """Only marker-scoped region should change."""
    path = tmp_path / "AGENTS.md"
    before = (
        "header line\n"
        "keep this exact\n"
        f"{AUTOGEN_START}\n"
        "old generated content\n"
        f"{AUTOGEN_END}\n"
        "trailer line\n"
    )
    path.write_text(before, encoding="utf-8")

    replace_autogen_block(path, "new generated content")

    after = path.read_text(encoding="utf-8")

    start_before = before.find(AUTOGEN_START)
    end_before = before.find(AUTOGEN_END, start_before) + len(AUTOGEN_END)
    start_after = after.find(AUTOGEN_START)
    end_after = after.find(AUTOGEN_END, start_after) + len(AUTOGEN_END)

    assert before[:start_before] == after[:start_after]
    assert before[end_before:] == after[end_after:]
    assert "new generated content" in after
    assert "old generated content" not in after


def test_docs_refresh_refuses_when_packet_repo_identity_mismatches(tmp_path: Path, monkeypatch) -> None:
    """docs refresh command should hard-fail on packet/repo project mismatch."""
    repo = tmp_path / "repo"
    repo.mkdir(parents=True, exist_ok=True)

    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)

    taskx_dir = repo / ".taskx"
    taskx_dir.mkdir(parents=True, exist_ok=True)
    (taskx_dir / "project.json").write_text(
        "{\n"
        '  "project_id": "taskx",\n'
        '  "project_slug": "taskX",\n'
        '  "repo_remote_hint": "taskX",\n'
        '  "packet_required_header": true\n'
        "}\n",
        encoding="utf-8",
    )

    run_dir = repo / "out" / "runs" / "RUN_X"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "TASK_PACKET.md").write_text(
        "# TASK_PACKET TP_0001 — Demo\n\n"
        "## PROJECT IDENTITY\n"
        "project_id: adops\n"
        "intended_repo: adops\n",
        encoding="utf-8",
    )

    runner = CliRunner()
    monkeypatch.chdir(repo)
    result = runner.invoke(
        cli,
        [
            "docs",
            "refresh-llm",
            "--run",
            str(run_dir),
            "--dry-run",
            "--tool-cmd",
            "echo '# autogen'",
            "--user-profile",
            "Hue",
        ],
    )

    assert result.exit_code == 1
    assert (
        "ERROR: Task Packet project_id 'adops' does not match repo project_id 'taskx'.\n"
        "Refusing to run. Use the correct repo or correct packet."
    ) in result.stdout
