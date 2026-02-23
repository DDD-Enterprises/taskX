import hashlib
import json
import zipfile
from pathlib import Path

from dopetask.pipeline.bundle.ingester import _build_case_index, ingest_bundle


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _make_zip(source_dir: Path, zip_path: Path) -> None:
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for file_path in sorted(p for p in source_dir.rglob("*") if p.is_file()):
            archive.write(file_path, file_path.relative_to(source_dir))


def test_build_case_index_categorization(tmp_path: Path) -> None:
    case_root = tmp_path / "case_root"
    files = {
        "taskx/task_queue.json": "{}",
        "taskx/runs/run-1/TASK_PACKET.md": "packet",
        "taskx/runs/run-1/RUN_SUMMARY.json": "summary",
        "repo/REPO_SNAPSHOT.json": "{}",
        "repo/logs/build.log": "log-data",
        "reports/audit.md": "report-data",
        "misc/unknown.txt": "unknown",
    }

    for rel_path, content in files.items():
        path = case_root / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    index = _build_case_index(case_root)
    categories = {entry["path"]: entry["category"] for entry in index["files"]}

    assert categories["taskx/task_queue.json"] == "taskx_task_queue"
    assert categories["taskx/runs/run-1/TASK_PACKET.md"] == "taskx_packet"
    assert categories["taskx/runs/run-1/RUN_SUMMARY.json"] == "taskx_run_artifact"
    assert categories["repo/REPO_SNAPSHOT.json"] == "repo_snapshot"
    assert categories["repo/logs/build.log"] == "repo_log"
    assert categories["reports/audit.md"] == "report"
    assert categories["misc/unknown.txt"] == "unknown"



def test_ingest_bundle_detects_integrity_mismatch(tmp_path: Path) -> None:
    bundle_root = tmp_path / "bundle_src"
    bundle_root.mkdir(parents=True)

    # Write extracted payload with actual (tampered) file contents
    tampered_content = "tampered"
    task_queue_path = bundle_root / "taskx" / "task_queue.json"
    task_queue_path.parent.mkdir(parents=True, exist_ok=True)
    task_queue_path.write_text(tampered_content, encoding="utf-8")

    manifest = {
        "schema_version": "1.0",
        "case_id": "CASE_MISMATCH",
        "generated_at": "1970-01-01T00:00:00Z",
        "bundle_manifest": {
            "sha256": "f" * 64,
            "source_label": "unit-test",
            "created_at": "1970-01-01T00:00:00Z",
        },
        "contents": {},
        "files": [
            {
                "path": "taskx/task_queue.json",
                "sha256": _sha("expected-content"),
                "size_bytes": len("expected-content"),
                "category": "taskx_task_queue",
            }
        ],
    }
    _write_json(bundle_root / "case" / "CASE_MANIFEST.json", manifest)

    zip_path = tmp_path / "CASE_MISMATCH.zip"
    _make_zip(bundle_root, zip_path)

    out_dir = tmp_path / "out_cases"
    result = ingest_bundle(zip_path=zip_path, output_dir=out_dir, timestamp_mode="deterministic")

    case_index_path = Path(result["case_index"])
    case_index = json.loads(case_index_path.read_text(encoding="utf-8"))

    assert case_index["integrity"]["status"] == "failed"
    assert case_index["integrity"]["mismatches_count"] >= 1

    mismatch_codes = {item["code"] for item in case_index["integrity"]["mismatches"]}
    assert "sha256_mismatch" in mismatch_codes
