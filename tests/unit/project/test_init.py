"""Tests for project initialization workflow."""

from pathlib import Path

from taskx.project.common import extract_block_content, read_pack_text
from taskx.project.init import init_project


def test_init_creates_files_when_missing(tmp_path: Path) -> None:
    """Init should create managed files, bundle defaults, and report."""
    out_dir = tmp_path / "project"

    result = init_project(out_dir=out_dir, preset="both")

    expected_files = {
        "PROJECT_INSTRUCTIONS.md",
        "CLAUDE.md",
        "CODEX.md",
        "AGENTS.md",
        "taskx_bundle.yaml",
        "PROJECT_INIT_REPORT.md",
    }
    assert expected_files.issubset({path.name for path in out_dir.iterdir()})
    assert Path(result["report_path"]).exists()

    for filename in ("PROJECT_INSTRUCTIONS.md", "CLAUDE.md", "CODEX.md", "AGENTS.md"):
        text = (out_dir / filename).read_text(encoding="utf-8")
        assert "<!-- TASKX:BEGIN -->" in text
        assert "<!-- TASKX:END -->" in text
        assert "<!-- CHATX:BEGIN -->" in text
        assert "<!-- CHATX:END -->" in text
        assert extract_block_content(text, "taskx") == read_pack_text("taskx")
        assert extract_block_content(text, "chatx") == read_pack_text("chatx")


def test_init_updates_existing_blocks_only(tmp_path: Path) -> None:
    """Init should update sentinel block content and keep user text outside blocks."""
    out_dir = tmp_path / "project"
    out_dir.mkdir(parents=True, exist_ok=True)

    original = (
        "# CLAUDE\n\n"
        "User section before blocks.\n\n"
        "<!-- TASKX:BEGIN -->\nold taskx payload\n<!-- TASKX:END -->\n\n"
        "<!-- CHATX:BEGIN -->\nold chatx payload\n<!-- CHATX:END -->\n\n"
        "User section after blocks.\n"
    )
    target = out_dir / "CLAUDE.md"
    target.write_text(original, encoding="utf-8")

    init_project(out_dir=out_dir, preset="taskx")
    updated = target.read_text(encoding="utf-8")

    assert "User section before blocks." in updated
    assert "User section after blocks." in updated
    assert extract_block_content(updated, "taskx") == read_pack_text("taskx")
    assert extract_block_content(updated, "chatx") == "(disabled)"


def test_init_appends_missing_blocks_without_clobbering_content(tmp_path: Path) -> None:
    """Init should append sentinel blocks when missing and preserve prior content."""
    out_dir = tmp_path / "project"
    out_dir.mkdir(parents=True, exist_ok=True)

    original = "# CODEX\n\nCustom project notes.\n"
    target = out_dir / "CODEX.md"
    target.write_text(original, encoding="utf-8")

    init_project(out_dir=out_dir, preset="none")
    updated = target.read_text(encoding="utf-8")

    assert updated.startswith(original)
    assert "<!-- TASKX:BEGIN -->" in updated
    assert "<!-- CHATX:BEGIN -->" in updated
    assert extract_block_content(updated, "taskx") == "(disabled)"
    assert extract_block_content(updated, "chatx") == "(disabled)"
