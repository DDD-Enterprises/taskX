from pathlib import Path

from typer.testing import CliRunner

from taskx.cli import cli
from taskx.project.common import SENTINELS
from taskx.project.toggles import project_status


RUNNER = CliRunner()
INSTRUCTION_FILES = (
    "PROJECT_INSTRUCTIONS.md",
    "CLAUDE.md",
    "CODEX.md",
    "AGENTS.md",
)


def _read_instruction_snapshots(project_dir: Path) -> dict[str, str]:
    return {
        filename: (project_dir / filename).read_text(encoding="utf-8")
        for filename in INSTRUCTION_FILES
    }


def _extract_block(text: str, pack_name: str) -> str:
    begin_marker, end_marker = SENTINELS[pack_name]
    begin_index = text.find(begin_marker)
    assert begin_index != -1
    content_start = begin_index + len(begin_marker)
    end_index = text.find(end_marker, content_start)
    assert end_index != -1
    return text[content_start:end_index].strip()


def _init_none(project_dir: Path) -> None:
    result = RUNNER.invoke(cli, ["project", "init", "--out", str(project_dir), "--preset", "none"])
    assert result.exit_code == 0, result.output


def test_enable_taskx_idempotent(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    _init_none(project_dir)

    first_enable = RUNNER.invoke(
        cli,
        ["project", "enable", "taskx", "--path", str(project_dir)],
    )
    assert first_enable.exit_code == 0, first_enable.output
    snapshot_after_first = _read_instruction_snapshots(project_dir)

    second_enable = RUNNER.invoke(
        cli,
        ["project", "enable", "taskx", "--path", str(project_dir)],
    )
    assert second_enable.exit_code == 0, second_enable.output
    snapshot_after_second = _read_instruction_snapshots(project_dir)

    assert snapshot_after_first == snapshot_after_second


def test_disable_taskx_idempotent(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    _init_none(project_dir)

    enable_result = RUNNER.invoke(
        cli,
        ["project", "enable", "taskx", "--path", str(project_dir)],
    )
    assert enable_result.exit_code == 0, enable_result.output

    first_disable = RUNNER.invoke(
        cli,
        ["project", "disable", "taskx", "--path", str(project_dir)],
    )
    assert first_disable.exit_code == 0, first_disable.output
    snapshot_after_first = _read_instruction_snapshots(project_dir)

    second_disable = RUNNER.invoke(
        cli,
        ["project", "disable", "taskx", "--path", str(project_dir)],
    )
    assert second_disable.exit_code == 0, second_disable.output
    snapshot_after_second = _read_instruction_snapshots(project_dir)

    assert snapshot_after_first == snapshot_after_second


def test_enable_chatx_does_not_remove_taskx(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    _init_none(project_dir)

    enable_taskx = RUNNER.invoke(
        cli,
        ["project", "enable", "taskx", "--path", str(project_dir)],
    )
    assert enable_taskx.exit_code == 0, enable_taskx.output

    before_chatx = _read_instruction_snapshots(project_dir)
    before_taskx_blocks = {
        filename: _extract_block(content, "taskx")
        for filename, content in before_chatx.items()
    }

    enable_chatx = RUNNER.invoke(
        cli,
        ["project", "enable", "chatx", "--path", str(project_dir)],
    )
    assert enable_chatx.exit_code == 0, enable_chatx.output

    after_chatx = _read_instruction_snapshots(project_dir)
    after_taskx_blocks = {
        filename: _extract_block(content, "taskx")
        for filename, content in after_chatx.items()
    }

    assert before_taskx_blocks == after_taskx_blocks
    assert all("Task packets are law" in block for block in after_taskx_blocks.values())


def test_project_status_reports_correctly(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    _init_none(project_dir)

    initial_status = project_status(project_dir)
    assert len(initial_status["files"]) == 4
    assert all(not item["packs"]["taskx"] for item in initial_status["files"])
    assert all(not item["packs"]["chatx"] for item in initial_status["files"])

    enable_taskx = RUNNER.invoke(
        cli,
        ["project", "enable", "taskx", "--path", str(project_dir)],
    )
    assert enable_taskx.exit_code == 0, enable_taskx.output
    enable_chatx = RUNNER.invoke(
        cli,
        ["project", "enable", "chatx", "--path", str(project_dir)],
    )
    assert enable_chatx.exit_code == 0, enable_chatx.output

    final_status = project_status(project_dir)
    assert len(final_status["files"]) == 4
    assert all(item["packs"]["taskx"] for item in final_status["files"])
    assert all(item["packs"]["chatx"] for item in final_status["files"])
