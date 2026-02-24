"""Invariants: metrics toggles must not mutate route planning artifacts."""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

from tests.unit.taskx.route_test_utils import create_taskx_repo, write_packet

REPO_ROOT = Path(__file__).resolve().parents[3]


def _run_taskx(args: list[str], *, env: dict[str, str]) -> None:
    run_env = dict(env)
    src_path = str(REPO_ROOT / "src")
    existing_pythonpath = run_env.get("PYTHONPATH")
    run_env["PYTHONPATH"] = f"{src_path}:{existing_pythonpath}" if existing_pythonpath else src_path

    result = subprocess.run(
        [sys.executable, "-m", "dopetask", *args],
        cwd=REPO_ROOT,
        env=run_env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"taskx command failed: {' '.join(args)}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"


def _artifact_hashes(out_dir: Path) -> dict[str, str]:
    files = sorted(path for path in out_dir.rglob("*") if path.is_file())
    hashes: dict[str, str] = {}
    for path in files:
        rel = str(path.relative_to(out_dir))
        hashes[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def test_metrics_env_on_off_do_not_change_route_plan_artifacts(tmp_path: Path) -> None:
    repo = create_taskx_repo(tmp_path / "repo")
    packet = write_packet(repo)

    base_env = os.environ.copy()
    base_env.update(
        {
            "TASKX_NEON": "0",
            "TASKX_STRICT": "0",
        }
    )
    env_off = dict(base_env)
    env_off.update(
        {
            "TASKX_METRICS": "0",
            "XDG_STATE_HOME": str(tmp_path / "state_off"),
        }
    )
    env_on = dict(base_env)
    env_on.update(
        {
            "TASKX_METRICS": "1",
            "XDG_STATE_HOME": str(tmp_path / "state_on"),
        }
    )

    _run_taskx(["route", "init", "--repo-root", str(repo)], env=env_off)
    _run_taskx(
        [
            "route",
            "plan",
            "--repo-root",
            str(repo),
            "--packet",
            str(packet),
            "--out",
            "out/metrics_off/ROUTE_PLAN.json",
        ],
        env=env_off,
    )
    _run_taskx(
        [
            "route",
            "plan",
            "--repo-root",
            str(repo),
            "--packet",
            str(packet),
            "--out",
            "out/metrics_on/ROUTE_PLAN.json",
        ],
        env=env_on,
    )

    off_hashes = _artifact_hashes(repo / "out" / "metrics_off")
    on_hashes = _artifact_hashes(repo / "out" / "metrics_on")
    assert on_hashes == off_hashes


def test_metrics_persistent_opt_in_does_not_change_route_plan_artifacts(tmp_path: Path) -> None:
    repo = create_taskx_repo(tmp_path / "repo")
    packet = write_packet(repo)

    env = os.environ.copy()
    env.update(
        {
            "XDG_STATE_HOME": str(tmp_path / "state"),
            "TASKX_NEON": "0",
            "TASKX_STRICT": "0",
        }
    )

    _run_taskx(["route", "init", "--repo-root", str(repo)], env=env)
    _run_taskx(["metrics", "enable"], env=env)
    _run_taskx(
        [
            "route",
            "plan",
            "--repo-root",
            str(repo),
            "--packet",
            str(packet),
            "--out",
            "out/persistent_on/ROUTE_PLAN.json",
        ],
        env=env,
    )

    _run_taskx(["metrics", "disable"], env=env)
    _run_taskx(
        [
            "route",
            "plan",
            "--repo-root",
            str(repo),
            "--packet",
            str(packet),
            "--out",
            "out/persistent_off/ROUTE_PLAN.json",
        ],
        env=env,
    )

    on_hashes = _artifact_hashes(repo / "out" / "persistent_on")
    off_hashes = _artifact_hashes(repo / "out" / "persistent_off")
    assert on_hashes == off_hashes
