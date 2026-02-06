"""Tests for task packet manifest generation and replay checks."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import validate

from taskx.manifest import (
    append_command_record,
    check_manifest,
    finalize_manifest,
    get_timestamp,
    init_manifest,
    load_manifest,
    save_manifest,
)


def _schema_path() -> Path:
    return Path(__file__).resolve().parents[3] / "schemas" / "task_packet_manifest.schema.json"


def _load_schema() -> dict:
    return json.loads(_schema_path().read_text(encoding="utf-8"))


def test_manifest_generation_is_schema_valid(tmp_path: Path) -> None:
    run_dir = tmp_path / "RUN_DETERMINISTIC"
    init_manifest(
        run_dir=run_dir,
        task_packet_id="TASKX_A24",
        mode="ACT",
        timestamp_mode="deterministic",
    )

    appended = append_command_record(
        run_dir=run_dir,
        cmd=["taskx", "gate-allowlist", "--token", "super-secret-token"],
        cwd=tmp_path,
        exit_code=0,
        stdout_text="gate passed",
        stderr_text="",
        timestamp_mode="deterministic",
        expected_artifacts=["ALLOWLIST_DIFF.json"],
        started_at=get_timestamp("deterministic"),
        ended_at=get_timestamp("deterministic"),
    )

    assert appended is True

    manifest = load_manifest(run_dir)
    assert manifest is not None
    validate(instance=manifest, schema=_load_schema())
    assert manifest["commands"][0]["cmd"][3] == "[REDACTED]"


def test_manifest_command_ordering_is_deterministic(tmp_path: Path) -> None:
    run_dir = tmp_path / "RUN_ORDER"
    init_manifest(
        run_dir=run_dir,
        task_packet_id="TASKX_A24",
        mode="ACT",
        timestamp_mode="deterministic",
    )
    manifest = load_manifest(run_dir)
    assert manifest is not None

    # Intentionally write out-of-order commands and verify save canonicalizes ordering.
    manifest["commands"] = [
        {
            "idx": 2,
            "cmd": "taskx promote-run --run /tmp/RUN_ORDER",
            "cwd": str(tmp_path),
            "started_at": "1970-01-01T00:00:00Z",
            "ended_at": "1970-01-01T00:00:00Z",
            "exit_code": 0,
            "stdout_path": "_manifest_logs/command_0002.stdout.log",
            "stderr_path": "_manifest_logs/command_0002.stderr.log",
            "truncated": False,
        },
        {
            "idx": 1,
            "cmd": "taskx gate-allowlist --run /tmp/RUN_ORDER",
            "cwd": str(tmp_path),
            "started_at": "1970-01-01T00:00:00Z",
            "ended_at": "1970-01-01T00:00:00Z",
            "exit_code": 0,
            "stdout_path": "_manifest_logs/command_0001.stdout.log",
            "stderr_path": "_manifest_logs/command_0001.stderr.log",
            "truncated": False,
        },
    ]
    finalize_manifest(
        manifest=manifest,
        artifacts_expected=["PROMOTION.json", "ALLOWLIST_DIFF.json"],
        artifacts_found=["ALLOWLIST_DIFF.json"],
        status="failed",
    )
    save_manifest(manifest, run_dir)

    rendered_first = (run_dir / "TASK_PACKET_MANIFEST.json").read_text(encoding="utf-8")
    reloaded = load_manifest(run_dir)
    assert reloaded is not None
    assert [item["idx"] for item in reloaded["commands"]] == [1, 2]

    save_manifest(reloaded, run_dir)
    rendered_second = (run_dir / "TASK_PACKET_MANIFEST.json").read_text(encoding="utf-8")
    assert rendered_first == rendered_second


def test_manifest_check_detects_missing_artifacts(tmp_path: Path) -> None:
    run_dir = tmp_path / "RUN_CHECK"
    init_manifest(
        run_dir=run_dir,
        task_packet_id="TASKX_A24",
        mode="ACT",
        timestamp_mode="deterministic",
    )
    manifest = load_manifest(run_dir)
    assert manifest is not None

    finalize_manifest(
        manifest=manifest,
        artifacts_expected=["PLAN.md", "PROMOTION.json"],
        artifacts_found=[],
        status="failed",
    )
    save_manifest(manifest, run_dir)

    (run_dir / "PLAN.md").write_text("plan", encoding="utf-8")
    (run_dir / "UNEXPECTED.md").write_text("extra", encoding="utf-8")

    replay = check_manifest(run_dir)
    assert replay["missing"] == ["PROMOTION.json"]
    assert replay["extras"] == ["UNEXPECTED.md"]
