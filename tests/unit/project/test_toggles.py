"""Tests for directive pack toggles."""

from pathlib import Path

from dopetask.project.common import extract_block_content, read_pack_text
from dopetask.project.init import init_project
from dopetask.project.toggles import apply_pack, disable_pack, enable_pack, project_status


def test_apply_pack_creates_missing_file_from_template(tmp_path: Path) -> None:
    """apply_pack should create missing managed file and set requested block."""
    target = tmp_path / "CLAUDE.md"

    result = apply_pack(file_path=target, pack_name="taskx", enabled=True)

    assert result["status"] == "created"
    text = target.read_text(encoding="utf-8")
    assert "<!-- TASKX:BEGIN -->" in text
    assert "<!-- CHATX:BEGIN -->" in text
    assert extract_block_content(text, "taskx") == read_pack_text("taskx")


def test_apply_pack_appends_missing_block_without_clobber(tmp_path: Path) -> None:
    """apply_pack should append sentinel block when missing and keep existing text."""
    target = tmp_path / "AGENTS.md"
    original = "# AGENTS\n\nUser content that should remain untouched.\n"
    target.write_text(original, encoding="utf-8")

    result = apply_pack(file_path=target, pack_name="chatx", enabled=True)
    updated = target.read_text(encoding="utf-8")

    assert result["status"] == "updated"
    assert updated.startswith(original)
    assert extract_block_content(updated, "chatx") == read_pack_text("chatx")


def test_enable_disable_toggle_only_block_content(tmp_path: Path) -> None:
    """Enable/disable should only change target block content."""
    init_project(out_dir=tmp_path, preset="none")
    original = (tmp_path / "CODEX.md").read_text(encoding="utf-8")

    enable_pack(project_dir=tmp_path, pack_name="taskx")
    enabled = (tmp_path / "CODEX.md").read_text(encoding="utf-8")
    assert _mask_block(original, "taskx") == _mask_block(enabled, "taskx")
    assert extract_block_content(enabled, "taskx") != "(disabled)"

    disable_pack(project_dir=tmp_path, pack_name="taskx")
    disabled = (tmp_path / "CODEX.md").read_text(encoding="utf-8")
    assert _mask_block(enabled, "taskx") == _mask_block(disabled, "taskx")
    assert extract_block_content(disabled, "taskx") == "(disabled)"
    assert (tmp_path / "PROJECT_PATCH_REPORT.md").exists()


def test_project_status_reports_enabled_and_disabled(tmp_path: Path) -> None:
    """Status should report pack state per managed file."""
    init_project(out_dir=tmp_path, preset="none")
    enable_pack(project_dir=tmp_path, pack_name="chatx")

    status = project_status(project_dir=tmp_path)

    assert len(status["files"]) == 4
    for file_status in status["files"]:
        assert file_status["exists"] is True
        assert file_status["packs"]["taskx"] is False
        assert file_status["packs"]["chatx"] is True


def _mask_block(text: str, pack_name: str) -> str:
    if pack_name == "taskx":
        begin = "<!-- TASKX:BEGIN -->"
        end = "<!-- TASKX:END -->"
    else:
        begin = "<!-- CHATX:BEGIN -->"
        end = "<!-- CHATX:END -->"

    lines = text.splitlines()
    begin_idx = None
    end_idx = None
    for idx, line in enumerate(lines):
        if begin_idx is None and line.strip() == begin:
            begin_idx = idx
        if begin_idx is not None and line.strip() == end:
            end_idx = idx
            break

    if begin_idx is None or end_idx is None:
        return text

    masked = lines[: begin_idx + 1] + ["<BLOCK_CONTENT>"] + lines[end_idx:]
    return "\n".join(masked)
