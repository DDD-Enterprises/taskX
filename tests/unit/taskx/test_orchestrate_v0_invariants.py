"""Orchestrator v0 deterministic invariants."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

from typer.testing import CliRunner

from dopetask.artifacts import canonical_dumps, sha256_file
from dopetask.cli import cli
from dopetask.orchestrator import kernel
from dopetask.orchestrator.kernel import orchestrate
from tests.unit.taskx.route_test_utils import create_taskx_repo, write_availability


def _write_packet(repo_root: Path, payload: dict[str, Any], name: str = "packet.json") -> Path:
    packet_path = repo_root / name
    packet_path.write_text(canonical_dumps(payload), encoding="utf-8")
    return packet_path


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _artifact_bytes(run_dir: Path, filenames: list[str]) -> dict[str, bytes]:
    return {name: (run_dir / name).read_bytes() for name in filenames}


def _manual_packet() -> dict[str, Any]:
    return {
        "task_id": "manual-handoff",
        "execution_mode": "manual",
        "steps": ["alpha", "beta"],
    }


def test_orchestrate_refusal_writes_expected_artifacts(tmp_path: Path) -> None:
    repo = create_taskx_repo(tmp_path / "repo")
    packet = _write_packet(
        repo,
        {
            "task_id": "missing-availability",
            "execution_mode": "auto",
            "steps": ["alpha", "beta"],
        },
    )

    outcome = orchestrate(str(packet))
    assert outcome["status"] == "refused"

    run_dir = Path(outcome["run_dir"])
    assert (run_dir / "ROUTE_PLAN.json").exists()
    assert (run_dir / "REFUSAL_REPORT.json").exists()
    assert (run_dir / "ARTIFACT_INDEX.json").exists()

    artifact_index = _read_json(run_dir / "ARTIFACT_INDEX.json")
    artifact_names = {item["name"] for item in artifact_index["artifacts"]}
    written_files = {item.name for item in run_dir.iterdir() if item.is_file() and item.name != "ARTIFACT_INDEX.json"}
    assert artifact_names == written_files

    for item in artifact_index["artifacts"]:
        assert item["sha256"] == sha256_file(run_dir / item["path"])


def test_orchestrate_refusal_rerun_is_byte_identical(tmp_path: Path) -> None:
    repo = create_taskx_repo(tmp_path / "repo")
    packet = _write_packet(
        repo,
        {
            "task_id": "rerun-refusal",
            "execution_mode": "auto",
            "steps": ["alpha", "beta"],
        },
    )

    first = orchestrate(str(packet))
    run_dir = Path(first["run_dir"])
    first_bytes = _artifact_bytes(
        run_dir,
        ["ROUTE_PLAN.json", "REFUSAL_REPORT.json", "ARTIFACT_INDEX.json"],
    )

    second = orchestrate(str(packet))
    assert second["run_dir"] == first["run_dir"]
    second_bytes = _artifact_bytes(
        run_dir,
        ["ROUTE_PLAN.json", "REFUSAL_REPORT.json", "ARTIFACT_INDEX.json"],
    )

    assert first_bytes == second_bytes


def test_orchestrate_executes_only_selected_runner(monkeypatch, tmp_path: Path) -> None:
    repo = create_taskx_repo(tmp_path / "repo")
    write_availability(
        repo,
        policy_overrides={"min_total_score": 1, "escalation_ladder": ["gpt-5.3-codex"]},
        models={
            "gpt-5.3-codex": {
                "strengths": ["code_edit", "tests"],
                "cost_tier": "high",
                "context": "large",
            }
        },
        runners={
            "claude_code": {"available": False, "strengths": ["code_edit"]},
            "codex_desktop": {"available": True, "strengths": ["code_edit", "tests"]},
            "copilot_cli": {"available": False, "strengths": ["quick_commands"]},
        },
    )
    packet = _write_packet(
        repo,
        {
            "task_id": "mutual-exclusive",
            "execution_mode": "auto",
            "steps": ["alpha", "beta"],
        },
    )

    calls = {"codex": 0, "claude": 0, "copilot": 0}

    class CodexSpy:
        runner_id = "codex_desktop"

        def prepare(self, packet: dict[str, Any], route_plan: dict[str, Any]) -> dict[str, Any]:
            del packet, route_plan
            return {"runner_id": "codex_desktop", "step": "alpha", "model_id": "gpt-5.3-codex"}

        def run(self, runspec: dict[str, Any]) -> dict[str, Any]:
            del runspec
            calls["codex"] += 1
            return {
                "status": "ok",
                "runner_id": "codex_desktop",
                "step": "alpha",
                "model_id": "gpt-5.3-codex",
                "outputs": [],
            }

        def normalize(self, result: dict[str, Any]) -> dict[str, Any]:
            return result

    class ClaudeSpy:
        runner_id = "claude_code"

        def prepare(self, packet: dict[str, Any], route_plan: dict[str, Any]) -> dict[str, Any]:
            del packet, route_plan
            return {}

        def run(self, runspec: dict[str, Any]) -> dict[str, Any]:
            del runspec
            calls["claude"] += 1
            return {"status": "ok", "runner_id": "claude_code", "outputs": []}

        def normalize(self, result: dict[str, Any]) -> dict[str, Any]:
            return result

    class CopilotSpy:
        runner_id = "copilot_cli"

        def prepare(self, packet: dict[str, Any], route_plan: dict[str, Any]) -> dict[str, Any]:
            del packet, route_plan
            return {}

        def run(self, runspec: dict[str, Any]) -> dict[str, Any]:
            del runspec
            calls["copilot"] += 1
            return {"status": "ok", "runner_id": "copilot_cli", "outputs": []}

        def normalize(self, result: dict[str, Any]) -> dict[str, Any]:
            return result

    monkeypatch.setitem(kernel.RUNNER_ADAPTERS, "codex_desktop", CodexSpy)
    monkeypatch.setitem(kernel.RUNNER_ADAPTERS, "claude_code", ClaudeSpy)
    monkeypatch.setitem(kernel.RUNNER_ADAPTERS, "copilot_cli", CopilotSpy)

    outcome = orchestrate(str(packet))
    assert outcome["status"] == "ok"
    assert calls == {"codex": 1, "claude": 0, "copilot": 0}


def test_refusal_route_plan_preserves_ladder_and_step_order(tmp_path: Path) -> None:
    repo = create_taskx_repo(tmp_path / "repo")
    custom_ladder = ["sonnet-4.55", "gpt-5.3-codex", "haiku-4.5"]
    write_availability(
        repo,
        policy_overrides={"min_total_score": 999, "escalation_ladder": custom_ladder},
    )
    packet = _write_packet(
        repo,
        {
            "task_id": "refusal-order",
            "execution_mode": "auto",
            "steps": ["alpha", "beta"],
        },
    )

    outcome = orchestrate(str(packet))
    assert outcome["status"] == "refused"
    route_plan = _read_json(Path(outcome["run_dir"]) / "ROUTE_PLAN.json")
    assert route_plan["policy"]["escalation_ladder"] == custom_ladder
    assert [step["step"] for step in route_plan["steps"]] == ["alpha", "beta"]


def test_refusal_side_effects_do_not_change_git_status(tmp_path: Path) -> None:
    repo = create_taskx_repo(tmp_path / "repo")
    packet = _write_packet(
        repo,
        {
            "task_id": "side-effects",
            "execution_mode": "auto",
            "steps": ["alpha", "beta"],
        },
    )
    subprocess.run(
        ["git", "init"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    (repo / ".gitignore").write_text("out/\n", encoding="utf-8")

    before = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    orchestrate(str(packet))
    after = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout

    assert before == after


def test_manual_mode_emits_chunks_and_artifacts(tmp_path: Path) -> None:
    repo = create_taskx_repo(tmp_path / "repo")
    write_availability(repo, policy_overrides={"min_total_score": 1})
    packet = _write_packet(repo, _manual_packet())

    outcome = orchestrate(str(packet))
    assert outcome["status"] == "needs_handoff"
    run_dir = Path(outcome["run_dir"])
    assert (run_dir / "ROUTE_PLAN.json").exists()
    assert (run_dir / "RUN_REPORT.json").exists()
    assert (run_dir / "ARTIFACT_INDEX.json").exists()

    route_plan = _read_json(run_dir / "ROUTE_PLAN.json")
    assert [chunk["step"] for chunk in route_plan["handoff_chunks"]] == ["alpha", "beta"]

    runner = CliRunner()
    cli_result = runner.invoke(cli, ["orchestrate", str(packet)])
    assert cli_result.exit_code == 2
    assert "HANDOFF CHUNK 1/2 (alpha)" in cli_result.stdout
    assert "HANDOFF CHUNK 2/2 (beta)" in cli_result.stdout


def test_manual_mode_rerun_json_artifacts_are_identical(tmp_path: Path) -> None:
    repo = create_taskx_repo(tmp_path / "repo")
    write_availability(repo, policy_overrides={"min_total_score": 1})
    packet = _write_packet(repo, _manual_packet())

    first = orchestrate(str(packet))
    run_dir = Path(first["run_dir"])
    first_bytes = _artifact_bytes(run_dir, ["ROUTE_PLAN.json", "RUN_REPORT.json"])

    second = orchestrate(str(packet))
    assert second["run_dir"] == first["run_dir"]
    second_bytes = _artifact_bytes(run_dir, ["ROUTE_PLAN.json", "RUN_REPORT.json"])
    assert first_bytes == second_bytes


def test_manual_handoff_chunks_do_not_include_timestamps(tmp_path: Path) -> None:
    repo = create_taskx_repo(tmp_path / "repo")
    write_availability(repo, policy_overrides={"min_total_score": 1})
    packet = _write_packet(repo, _manual_packet())

    outcome = orchestrate(str(packet))
    route_plan = _read_json(Path(outcome["run_dir"]) / "ROUTE_PLAN.json")

    timestamp_pattern = re.compile(
        r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z?\b|\b\d{2}:\d{2}:\d{2}\b"
    )
    for chunk in route_plan["handoff_chunks"]:
        assert not timestamp_pattern.search(chunk["instructions_block"])
