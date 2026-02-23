"""Tests for project master mode and doctor workflows."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from dopetask.project.common import MANAGED_FILES, SENTINELS, apply_block_content, read_pack_text
from dopetask.project.doctor import check_project, fix_project
from dopetask.project.init import init_project
from dopetask.project.mode import set_mode


def _hash_file(path: Path) -> str:
    return sha256(path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()


def _check_ids(report: dict) -> dict[str, dict]:
    return {item["id"]: item for item in report["checks"]}


def test_mode_set_idempotent(tmp_path: Path) -> None:
    project_dir = tmp_path / "proj"
    init_project(out_dir=project_dir, preset="none")

    first = set_mode(project_dir, "both")
    snapshot_after_first = {
        filename: _hash_file(project_dir / filename)
        for filename in MANAGED_FILES
    }

    second = set_mode(project_dir, "both")
    snapshot_after_second = {
        filename: _hash_file(project_dir / filename)
        for filename in MANAGED_FILES
    }

    assert first["mode"] == "both"
    assert second["mode"] == "both"
    assert second["changed_files"] == []
    assert snapshot_after_first == snapshot_after_second


def test_doctor_detects_missing_files(tmp_path: Path) -> None:
    project_dir = tmp_path / "proj"
    init_project(out_dir=project_dir, preset="none")
    (project_dir / "AGENTS.md").unlink()

    report = check_project(project_dir)
    checks = _check_ids(report)

    assert report["status"] == "fail"
    assert checks["files_present"]["status"] == "fail"
    assert "AGENTS.md" in checks["files_present"]["message"]


def test_doctor_detects_missing_sentinels(tmp_path: Path) -> None:
    project_dir = tmp_path / "proj"
    init_project(out_dir=project_dir, preset="none")

    target = project_dir / "CODEX.md"
    text = target.read_text(encoding="utf-8")
    begin_marker, end_marker = SENTINELS["chatx"]
    start = text.find(begin_marker)
    end = text.find(end_marker, start)
    assert start != -1
    assert end != -1
    target.write_text(text[:start] + text[end + len(end_marker) :], encoding="utf-8")

    report = check_project(project_dir)
    checks = _check_ids(report)

    assert report["status"] == "fail"
    assert checks["sentinel_integrity"]["status"] == "fail"
    assert "CODEX.md" in checks["sentinel_integrity"]["files"]


def test_doctor_fix_creates_files_and_prompts(tmp_path: Path) -> None:
    project_dir = tmp_path / "proj"
    init_project(out_dir=project_dir, preset="none")
    (project_dir / "PROJECT_INSTRUCTIONS.md").unlink()

    report = fix_project(project_dir, mode="both")
    checks = _check_ids(report)

    assert report["status"] == "pass"
    assert report["detected_mode"] == "both"
    assert checks["files_present"]["status"] == "pass"
    assert checks["supervisor_prompt"]["status"] == "pass"

    for filename in MANAGED_FILES:
        assert (project_dir / filename).exists()

    prompt_path = project_dir / "generated" / "SUPERVISOR_PRIMING_PROMPT.txt"
    assert prompt_path.exists()
    prompt_text = prompt_path.read_text(encoding="utf-8")
    assert "mode: both" in prompt_text


def test_doctor_detects_inconsistent_mode(tmp_path: Path) -> None:
    project_dir = tmp_path / "proj"
    init_project(out_dir=project_dir, preset="none")

    one_file = project_dir / "AGENTS.md"
    original = one_file.read_text(encoding="utf-8")
    updated, _ = apply_block_content(original, "chatx", read_pack_text("chatx"))
    one_file.write_text(updated, encoding="utf-8")

    report = check_project(project_dir)
    checks = _check_ids(report)

    assert report["status"] == "fail"
    assert report["detected_mode"] == "inconsistent"
    assert checks["pack_status_consistency"]["status"] == "fail"
    assert checks["pack_status_consistency"]["files"] == ["AGENTS.md"]
