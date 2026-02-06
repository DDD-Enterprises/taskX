import json
from pathlib import Path

from taskx.pipeline.case.auditor import (
    _aggregate_anomalies,
    _detect_verification_gaps,
    audit_case,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_aggregate_anomalies_counts_and_runs() -> None:
    summaries = [
        {"run_id": "run-1", "status": {"anomalies": ["missing output", "timeout"]}},
        {"run_id": "run-2", "status": {"anomalies": ["missing output"]}},
    ]

    result = _aggregate_anomalies(summaries)

    assert result["total_unique"] == 2
    assert result["top"][0]["text"] == "missing output"
    assert result["top"][0]["count"] == 2
    assert result["top"][0]["run_ids"] == ["run-1", "run-2"]



def test_detect_verification_gaps_percentages() -> None:
    summaries = [
        {
            "run_id": "run-1",
            "status": {
                "checklist_completed": True,
                "verification_commands_listed": False,
                "verification_outputs_present": False,
                "anomalies": ["missing outputs"],
            },
        },
        {
            "run_id": "run-2",
            "status": {
                "checklist_completed": False,
                "verification_commands_listed": True,
                "verification_outputs_present": True,
                "anomalies": ["checklist incomplete"],
            },
        },
    ]

    result = _detect_verification_gaps(summaries)

    assert result["runs_with_summaries"] == 2
    assert result["pct_checklist_incomplete"] == 50.0
    assert result["pct_verification_commands_missing"] == 50.0
    assert result["pct_verification_outputs_missing"] == 50.0
    assert "missing outputs" in result["top_anomalies"]



def test_audit_case_handles_no_runs(tmp_path: Path) -> None:
    case_dir = tmp_path / "CASE_EMPTY"
    case_dir.mkdir(parents=True)

    _write_json(
        case_dir / "CASE_INDEX.json",
        {
            "schema_version": "1.0",
            "case_id": "CASE_EMPTY",
            "ingested_at": "1970-01-01T00:00:00Z",
            "zip_sha256": "a" * 64,
            "integrity": {"status": "passed", "mismatches_count": 0, "mismatches": []},
            "counts": {
                "files_total": 1,
                "logs_included": 0,
                "logs_skipped": 0,
                "run_dirs": 0,
                "packets": 0,
            },
            "files": [
                {
                    "path": "case/CASE_MANIFEST.json",
                    "sha256": "b" * 64,
                    "size_bytes": 10,
                    "category": "unknown",
                }
            ],
        },
    )

    out_dir = tmp_path / "reports"
    result = audit_case(case_dir=case_dir, output_dir=out_dir, timestamp_mode="deterministic")

    findings = json.loads(Path(result["findings"]).read_text(encoding="utf-8"))
    assert findings["run_coverage"]["runs_found"] == 0
    assert findings["run_coverage"]["run_summaries_found"] == 0

    report_text = Path(result["report"]).read_text(encoding="utf-8")
    assert "0 runs found" in report_text

    recommendations = json.loads(Path(result["recommendations"]).read_text(encoding="utf-8"))
    assert recommendations["recommendations"]
