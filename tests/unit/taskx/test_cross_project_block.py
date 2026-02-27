"""Cross-project hard block and WIP rescue patch tests."""

import subprocess
from pathlib import Path

from typer.testing import CliRunner

from dopetask.cli import cli

RUNNER = CliRunner()


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        check=True,
        text=True,
    )


def _init_fake_repo(repo: Path) -> None:
    repo.mkdir(parents=True)
    _git(repo, "init")


def test_guarded_command_blocks_without_dopetaskroot_even_with_pyproject(
    tmp_path: Path,
    monkeypatch,
) -> None:
    fake_repo = (tmp_path / "fake_repo").resolve()
    _init_fake_repo(fake_repo)
    (fake_repo / "pyproject.toml").write_text('[project]\nname = "dopetask"\n', encoding="utf-8")
    run_dir = fake_repo / "out" / "runs" / "RUN_DETERMINISTIC"
    run_dir.mkdir(parents=True)

    monkeypatch.chdir(fake_repo)
    result = RUNNER.invoke(
        cli,
        [
            "gate-allowlist",
            "--run",
            str(run_dir),
            "--timestamp-mode",
            "deterministic",
        ],
    )

    assert result.exit_code != 0
    normalized = " ".join(result.output.split())
    assert "This is not a dopeTask repo (missing .dopetaskroot). Refusing to run stateful command." in normalized
    assert "Detected repo root:" in normalized
    assert "CWD:" in normalized
    assert str(fake_repo.name) in normalized


def test_guarded_command_writes_rescue_patch_and_exits_non_zero(
    tmp_path: Path,
    monkeypatch,
) -> None:
    fake_repo = (tmp_path / "fake_repo").resolve()
    _init_fake_repo(fake_repo)
    tracked = fake_repo / "tracked.txt"
    tracked.write_text("base\n", encoding="utf-8")
    _git(fake_repo, "add", "tracked.txt")
    tracked.write_text("base\nchanged\n", encoding="utf-8")
    run_dir = fake_repo / "out" / "runs" / "RUN_DETERMINISTIC"
    run_dir.mkdir(parents=True)

    monkeypatch.chdir(fake_repo)
    result = RUNNER.invoke(
        cli,
        [
            "gate-allowlist",
            "--run",
            str(run_dir),
            "--timestamp-mode",
            "deterministic",
            "--rescue-patch",
            "auto",
        ],
    )

    assert result.exit_code != 0
    assert "Rescue patch written to:" in result.output

    rescue_root = fake_repo / "out" / "dopetask_rescue"
    rescue_patches = list(rescue_root.glob("*/rescue.patch"))
    assert len(rescue_patches) == 1

    patch_content = rescue_patches[0].read_text(encoding="utf-8")
    assert "git status --porcelain" in patch_content
    assert "git diff" in patch_content
    assert "tracked.txt" in patch_content
