"""Tests for TaskX local opt-in metrics CLI commands."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from typer.testing import CliRunner

from dopetask.cli import cli
from dopetask.metrics import load_metrics, resolve_metrics_path

RUNNER = CliRunner()
REPO_ROOT = Path(__file__).resolve().parents[3]


def _run_taskx(args: list[str], *, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    """Run `python -m taskx ...` and return completed process."""
    run_env = dict(env)
    src_path = str(REPO_ROOT / "src")
    existing_pythonpath = run_env.get("PYTHONPATH")
    run_env["PYTHONPATH"] = f"{src_path}:{existing_pythonpath}" if existing_pythonpath else src_path

    return subprocess.run(
        [sys.executable, "-m", "taskx", *args],
        cwd=REPO_ROOT,
        env=run_env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_metrics_status_defaults_to_disabled(tmp_path: Path, monkeypatch) -> None:
    state_home = tmp_path / "state"
    monkeypatch.setenv("XDG_STATE_HOME", str(state_home))
    monkeypatch.delenv("TASKX_METRICS", raising=False)

    result = RUNNER.invoke(cli, ["metrics", "status"])
    assert result.exit_code == 0, result.output

    metrics_path = resolve_metrics_path(env={"XDG_STATE_HOME": str(state_home)}, home=tmp_path)
    assert f"path={metrics_path}" in result.output
    assert "env_enabled=0" in result.output
    assert "persistent_enabled=0" in result.output
    assert "effective_enabled=0" in result.output
    assert not metrics_path.exists()


def test_metrics_enable_disable_show_and_reset(tmp_path: Path, monkeypatch) -> None:
    state_home = tmp_path / "state"
    monkeypatch.setenv("XDG_STATE_HOME", str(state_home))
    monkeypatch.delenv("TASKX_METRICS", raising=False)

    enabled = RUNNER.invoke(cli, ["metrics", "enable"])
    assert enabled.exit_code == 0, enabled.output
    assert "metrics_enabled=1" in enabled.output

    shown = RUNNER.invoke(cli, ["metrics", "show"])
    assert shown.exit_code == 0, shown.output
    payload = json.loads(shown.output)
    assert payload["enabled"] is True
    assert isinstance(payload["commands"], dict)

    env = os.environ.copy()
    env.update(
        {
            "XDG_STATE_HOME": str(state_home),
            "TASKX_METRICS": "1",
            "TASKX_NEON": "0",
            "TASKX_STRICT": "0",
        }
    )
    help_result = _run_taskx(["--help"], env=env)
    assert help_result.returncode == 0, help_result.stderr

    reset = RUNNER.invoke(cli, ["metrics", "reset"])
    assert reset.exit_code == 0, reset.output
    assert "metrics_commands_reset=1" in reset.output

    metrics_path = resolve_metrics_path(env={"XDG_STATE_HOME": str(state_home)}, home=tmp_path)
    payload_after_reset = load_metrics(metrics_path)
    assert payload_after_reset["commands"] == {}

    disabled = RUNNER.invoke(cli, ["metrics", "disable"])
    assert disabled.exit_code == 0, disabled.output
    assert "metrics_enabled=0" in disabled.output

    status = RUNNER.invoke(cli, ["metrics", "status"])
    assert status.exit_code == 0, status.output
    assert "persistent_enabled=0" in status.output


def test_metrics_env_opt_in_counts_help_and_version(tmp_path: Path) -> None:
    state_home = tmp_path / "state"
    env = os.environ.copy()
    env.update(
        {
            "XDG_STATE_HOME": str(state_home),
            "TASKX_METRICS": "1",
            "TASKX_NEON": "0",
            "TASKX_STRICT": "0",
        }
    )

    help_result = _run_taskx(["--help"], env=env)
    assert help_result.returncode == 0, help_result.stderr

    version_result = _run_taskx(["--version"], env=env)
    assert version_result.returncode == 0, version_result.stderr

    metrics_path = resolve_metrics_path(env={"XDG_STATE_HOME": str(state_home)}, home=tmp_path)
    payload = load_metrics(metrics_path)
    commands = payload.get("commands", {})

    assert isinstance(commands, dict)
    assert commands.get("--help", 0) >= 1
    assert commands.get("--version", 0) >= 1
    assert payload["enabled"] is False
