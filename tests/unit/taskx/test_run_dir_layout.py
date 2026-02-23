"""Tests for canonical run directory layout and stateful artifact containment."""

from __future__ import annotations

import importlib
from pathlib import Path
from types import SimpleNamespace

from typer.testing import CliRunner

import dopetask.cli as cli_module
from dopetask.cli import cli
from dopetask.obs.run_artifacts import get_default_run_root, resolve_run_dir


def _file_snapshot(root: Path) -> set[str]:
    """Return a stable set of file paths relative to root."""
    return {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}


def test_deterministic_mode_uses_stable_run_id_and_path(tmp_path: Path) -> None:
    """Deterministic mode should always target RUN_DETERMINISTIC."""
    run_root = tmp_path / "runs"
    resolved = resolve_run_dir(
        run=None,
        run_root=run_root,
        timestamp_mode="deterministic",
    )
    assert resolved == (run_root / "RUN_DETERMINISTIC").resolve()


def test_taskx_run_root_env_is_respected(tmp_path: Path, monkeypatch) -> None:
    """TASKX_RUN_ROOT should override repo/cwd defaults."""
    env_root = tmp_path / "env-runs"
    monkeypatch.setenv("TASKX_RUN_ROOT", str(env_root))

    resolved = get_default_run_root(cwd=tmp_path / "work")
    assert resolved == env_root.resolve()


def test_stateful_commands_write_only_inside_run_dir(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Stateful commands should only emit artifacts under the selected run dir."""
    runner = CliRunner()
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    run_dir = workspace / "runs" / "RUN_DETERMINISTIC"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "RUN_ENVELOPE.json").write_text("{}", encoding="utf-8")
    (run_dir / "ALLOWLIST_DIFF.json").write_text(
        '{"violations":{"count":0,"items":[]},"changed_files":{"disallowed":[]}}',
        encoding="utf-8",
    )

    def fake_guard(_: bool, rescue_patch: str | None = None) -> Path:
        del rescue_patch
        return workspace

    def fake_allowlist_gate(*, run_dir: Path, out_dir: Path | None = None, **kwargs):
        del kwargs
        target = out_dir or run_dir
        target.mkdir(parents=True, exist_ok=True)
        (target / "ALLOWLIST_DIFF.json").write_text("{}", encoding="utf-8")
        (target / "VIOLATIONS.md").write_text("# violations\n", encoding="utf-8")
        return SimpleNamespace(violations=[])

    def fake_promote_run(*, run_dir: Path, out_dir: Path | None = None, **kwargs):
        del kwargs
        target = out_dir or run_dir
        target.mkdir(parents=True, exist_ok=True)
        (target / "PROMOTION.json").write_text('{"status":"passed"}', encoding="utf-8")
        return SimpleNamespace(status="passed")

    def fake_commit_run(*, run_dir: Path, **kwargs):
        del kwargs
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "COMMIT_RUN.json").write_text("{}", encoding="utf-8")
        return {
            "status": "passed",
            "git": {"branch": "main", "head_after": "abc123"},
            "allowlist": {"staged_files": ["src/example.py"]},
        }

    def fake_ci_gate(*, out_dir: Path, run_dir: Path | None = None, **kwargs):
        del kwargs
        target = out_dir
        target.mkdir(parents=True, exist_ok=True)
        (target / "CI_GATE_REPORT.json").write_text("{}", encoding="utf-8")
        (target / "CI_GATE_REPORT.md").write_text("# ci-gate\n", encoding="utf-8")
        return SimpleNamespace(
            status="passed",
            doctor={"status": "passed"},
            promotion={
                "required": True,
                "validated": True,
                "run_dir": str((run_dir or target).resolve()),
            },
            checks={"passed": 2, "failed": 0, "warnings": 0},
        )

    monkeypatch.setattr(cli_module, "_check_repo_guard", fake_guard)
    monkeypatch.setattr(cli_module, "run_allowlist_gate", fake_allowlist_gate)
    monkeypatch.setattr(cli_module, "promote_run_impl", fake_promote_run)
    commit_run_module = importlib.import_module("taskx.git.commit_run")
    monkeypatch.setattr(commit_run_module, "commit_run", fake_commit_run)
    monkeypatch.setattr("taskx.ci_gate.run_ci_gate", fake_ci_gate)

    before = _file_snapshot(workspace)

    result_gate = runner.invoke(
        cli,
        ["gate-allowlist", "--run", str(run_dir), "--timestamp-mode", "deterministic"],
    )
    assert result_gate.exit_code == 0

    result_promote = runner.invoke(
        cli,
        ["promote-run", "--run", str(run_dir), "--timestamp-mode", "deterministic"],
    )
    assert result_promote.exit_code == 0

    result_commit = runner.invoke(
        cli,
        ["commit-run", "--run", str(run_dir), "--timestamp-mode", "deterministic", "--allow-unpromoted"],
    )
    assert result_commit.exit_code == 0

    result_ci = runner.invoke(
        cli,
        ["ci-gate", "--run", str(run_dir), "--timestamp-mode", "deterministic"],
    )
    assert result_ci.exit_code == 0

    after = _file_snapshot(workspace)
    created = after - before

    expected_prefix = run_dir.relative_to(workspace).as_posix() + "/"
    assert created
    assert all(path.startswith(expected_prefix) for path in created)

    assert (run_dir / "ALLOWLIST_DIFF.json").exists()
    assert (run_dir / "VIOLATIONS.md").exists()
    assert (run_dir / "PROMOTION_TOKEN.json").exists()
    assert (run_dir / "COMMIT_RUN.json").exists()
