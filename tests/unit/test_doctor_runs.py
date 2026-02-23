"""Verify taskx doctor runs to completion in a clean environment."""
from pathlib import Path

from dopetask.doctor import run_doctor


def test_doctor_passes_deterministic(tmp_path: Path):
    report = run_doctor(
        out_dir=tmp_path,
        timestamp_mode="deterministic",
        require_git=False,
    )
    assert report.status == "passed"
    assert (tmp_path / "DOCTOR_REPORT.json").exists()
    assert (tmp_path / "DOCTOR_REPORT.md").exists()
    assert report.checks["failed"] == 0


def test_doctor_deterministic_timestamp(tmp_path: Path):
    report = run_doctor(
        out_dir=tmp_path,
        timestamp_mode="deterministic",
        require_git=False,
    )
    assert report.generated_at == "1970-01-01T00:00:00Z"
