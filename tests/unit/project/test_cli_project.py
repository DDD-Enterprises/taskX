"""CLI tests for project init/toggle commands."""

from pathlib import Path

from typer.testing import CliRunner

from dopetask.cli import cli


def test_project_init_command(tmp_path: Path) -> None:
    """`dopetask project init` should create expected files."""
    runner = CliRunner()
    project_dir = tmp_path / "cli-project"

    result = runner.invoke(
        cli,
        ["project", "init", "--out", str(project_dir), "--preset", "both"],
    )

    assert result.exit_code == 0
    assert (project_dir / "PROJECT_INSTRUCTIONS.md").exists()
    assert (project_dir / "PROJECT_INIT_REPORT.md").exists()


def test_project_enable_disable_status_commands(tmp_path: Path) -> None:
    """Enable/disable/status commands should run and write patch report."""
    runner = CliRunner()
    project_dir = tmp_path / "cli-project"

    init_result = runner.invoke(
        cli,
        ["project", "init", "--out", str(project_dir), "--preset", "none"],
    )
    assert init_result.exit_code == 0

    enable_result = runner.invoke(
        cli,
        ["project", "enable", "dopetask", "--path", str(project_dir)],
    )
    assert enable_result.exit_code == 0
    assert (project_dir / "PROJECT_PATCH_REPORT.md").exists()

    status_result = runner.invoke(
        cli,
        ["project", "status", "--path", str(project_dir)],
    )
    assert status_result.exit_code == 0
    assert "dopetask=enabled" in status_result.stdout

    disable_result = runner.invoke(
        cli,
        ["project", "disable", "dopetask", "--path", str(project_dir)],
    )
    assert disable_result.exit_code == 0

