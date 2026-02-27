"""Bundle ingestion and integrity indexing utilities."""

from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from jsonschema import validate
from rich.console import Console

from dopetask.utils.schema_registry import get_schema_json

if TYPE_CHECKING:
    from pathlib import Path

DETERMINISTIC_TIMESTAMP = "1970-01-01T00:00:00Z"

console = Console()


def _timestamp(timestamp_mode: str) -> str:
    if timestamp_mode == "deterministic":
        return DETERMINISTIC_TIMESTAMP
    if timestamp_mode == "wallclock":
        return datetime.now(UTC).isoformat()
    raise ValueError(f"Invalid timestamp_mode: {timestamp_mode}")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _classify_path(rel_path: str) -> str:
    normalized = rel_path.replace("\\", "/")
    if normalized == "dopetask/task_queue.json":
        return "dopetask_task_queue"
    if normalized.startswith("dopetask/packets/") or (
        normalized.startswith("dopetask/runs/") and normalized.endswith("/TASK_PACKET.md")
    ):
        return "dopetask_packet"
    if normalized.startswith("dopetask/runs/"):
        return "dopetask_run_artifact"
    if normalized == "repo/REPO_SNAPSHOT.json":
        return "repo_snapshot"
    if normalized.startswith("repo/logs/") or normalized == "repo/LOG_INDEX.json":
        return "repo_log"
    if normalized.startswith("reports/"):
        return "report"
    return "unknown"


def _build_case_index(
    case_root: Path,
    *,
    case_id: str | None = None,
    integrity: dict[str, Any] | None = None,
    timestamp_mode: str = "deterministic",
) -> dict[str, Any]:
    """Build deterministic CASE_INDEX payload for an extracted bundle."""
    files: list[dict[str, Any]] = []
    for path in sorted(p for p in case_root.rglob("*") if p.is_file()):
        rel = path.relative_to(case_root).as_posix()
        files.append(
            {
                "path": rel,
                "sha256": _sha256_file(path),
                "size_bytes": path.stat().st_size,
                "category": _classify_path(rel),
            }
        )

    run_dirs = sorted(
        p
        for p in (case_root / "dopetask" / "runs").glob("*")
        if p.is_dir()
    ) if (case_root / "dopetask" / "runs").exists() else []
    packet_files = sorted((case_root / "dopetask").glob("packets/*.md")) if (case_root / "dopetask").exists() else []
    logs_included = sum(1 for entry in files if str(entry.get("category")) == "repo_log")
    logs_skipped = 0

    effective_integrity = integrity or {
        "status": "UNKNOWN",
        "mismatches_count": 0,
        "mismatches": [],
    }
    effective_integrity.setdefault("status", "UNKNOWN")
    effective_integrity.setdefault("mismatches_count", len(effective_integrity.get("mismatches", [])))
    effective_integrity.setdefault("mismatches", [])

    return {
        "schema_version": "1.0",
        "case_id": case_id or case_root.name,
        "ingested_at": _timestamp(timestamp_mode),
        "integrity": effective_integrity,
        "counts": {
            "files_total": len(files),
            "logs_included": logs_included,
            "logs_skipped": logs_skipped,
            "run_dirs": len(run_dirs),
            "packets": len(packet_files),
        },
        "files": files,
    }


def _validate_manifest_integrity(case_root: Path, manifest_data: dict[str, Any]) -> dict[str, Any]:
    """Validate file-level integrity against CASE_MANIFEST.files entries."""
    mismatches: list[dict[str, Any]] = []
    entries = manifest_data.get("files", [])
    if not isinstance(entries, list):
        return {
            "status": "failed",
            "mismatches_count": 1,
            "mismatches": [
                {
                    "code": "manifest_files_invalid",
                    "path": "case/CASE_MANIFEST.json",
                    "message": "`files` field must be a list when provided.",
                }
            ],
        }

    for entry in entries:
        if not isinstance(entry, dict):
            mismatches.append(
                {
                    "code": "manifest_entry_invalid",
                    "path": "case/CASE_MANIFEST.json",
                    "message": "Manifest file entry is not an object.",
                }
            )
            continue

        rel_path = entry.get("path")
        if not isinstance(rel_path, str) or not rel_path:
            mismatches.append(
                {
                    "code": "manifest_path_invalid",
                    "path": "case/CASE_MANIFEST.json",
                    "message": "Manifest file entry missing `path`.",
                }
            )
            continue

        target = case_root / rel_path
        if not target.exists() or not target.is_file():
            mismatches.append(
                {
                    "code": "missing_file",
                    "path": rel_path,
                    "message": "File listed in manifest is missing from bundle payload.",
                }
            )
            continue

        expected_sha = entry.get("sha256")
        if isinstance(expected_sha, str):
            actual_sha = _sha256_file(target)
            if actual_sha != expected_sha:
                mismatches.append(
                    {
                        "code": "sha256_mismatch",
                        "path": rel_path,
                        "message": f"Expected {expected_sha}, got {actual_sha}.",
                    }
                )

        expected_size = entry.get("size_bytes")
        if isinstance(expected_size, int):
            actual_size = target.stat().st_size
            if actual_size != expected_size:
                mismatches.append(
                    {
                        "code": "size_mismatch",
                        "path": rel_path,
                        "message": f"Expected {expected_size} bytes, got {actual_size}.",
                    }
                )

    status = "passed" if not mismatches else "failed"
    return {
        "status": status,
        "mismatches_count": len(mismatches),
        "mismatches": mismatches,
    }


def _write_case_index(case_root: Path, payload: dict[str, Any]) -> Path:
    index_path = case_root / "CASE_INDEX.json"
    index_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return index_path


def _write_ingest_report(case_root: Path, payload: dict[str, Any]) -> Path:
    integrity = payload.get("integrity", {})
    status = str(integrity.get("status", "UNKNOWN"))
    mismatch_count = int(integrity.get("mismatches_count", 0))
    report = "\n".join(
        [
            "# Case Ingest Report",
            "",
            f"- case_id: `{payload.get('case_id', case_root.name)}`",
            f"- integrity_status: `{status}`",
            f"- mismatches_count: `{mismatch_count}`",
            "",
            "## Notes",
            "- CASE_INDEX.json was generated from extracted bundle payload.",
        ]
    )
    report_path = case_root / "CASE_INGEST_REPORT.md"
    report_path.write_text(report + "\n", encoding="utf-8")
    return report_path


class BundleIngester:
    """Handles secure ingestion and validation of case bundles."""

    def __init__(self, out_dir: Path):
        self.out_dir = out_dir.resolve()

    def extract_bundle(self, zip_path: Path) -> Path:
        """Securely extract bundle to out_dir."""
        if not zip_path.exists():
            raise FileNotFoundError(f"Bundle zip not found: {zip_path}")

        extract_root = self.out_dir / zip_path.stem
        if extract_root.exists():
            shutil.rmtree(extract_root)
        extract_root.mkdir(parents=True, exist_ok=True)

        console.print(f"[cyan]Extracting {zip_path.name} to {extract_root}...[/cyan]")
        with zipfile.ZipFile(zip_path, "r") as archive:
            for member in archive.infolist():
                filename = member.filename
                if filename.startswith("/") or ".." in filename:
                    raise ValueError(f"Malicious filename detected in zip: {filename}")
            archive.extractall(extract_root)

        return extract_root

    def validate_manifest(self, case_dir: Path) -> dict[str, Any]:
        """Validate CASE_MANIFEST.json against schema contract."""
        manifest_path = case_dir / "case" / "CASE_MANIFEST.json"
        if not manifest_path.exists():
            raise FileNotFoundError(f"CASE_MANIFEST.json missing in {case_dir}")

        with manifest_path.open(encoding="utf-8") as handle:
            manifest_data = json.load(handle)
        if not isinstance(manifest_data, dict):
            raise ValueError("CASE_MANIFEST.json must contain a JSON object")

        schema = get_schema_json("case_bundle")
        validate(instance=manifest_data, schema=schema)
        return manifest_data

    def generate_case_index(
        self,
        case_dir: Path,
        *,
        manifest_data: dict[str, Any],
        timestamp_mode: str,
    ) -> Path:
        """Generate CASE_INDEX.json with integrity results."""
        integrity = _validate_manifest_integrity(case_dir, manifest_data)
        index_payload = _build_case_index(
            case_dir,
            case_id=str(manifest_data.get("case_id", case_dir.name)),
            integrity=integrity,
            timestamp_mode=timestamp_mode,
        )
        return _write_case_index(case_dir, index_payload)

    def ingest(self, zip_path: Path, timestamp_mode: str = "deterministic") -> Path:
        """Extract and validate a bundle, then generate CASE_INDEX."""
        case_dir = self.extract_bundle(zip_path)
        manifest_data = self.validate_manifest(case_dir)
        index_path = self.generate_case_index(
            case_dir,
            manifest_data=manifest_data,
            timestamp_mode=timestamp_mode,
        )
        console.print(f"[green]✓ Case index generated: {index_path.relative_to(case_dir)}[/green]")
        return case_dir


def ingest_bundle(zip_path: Path, output_dir: Path, timestamp_mode: str = "deterministic") -> dict[str, str]:
    """Public ingest entrypoint used by CLI/tests."""
    ingester = BundleIngester(output_dir)
    case_dir = ingester.extract_bundle(zip_path)
    manifest_data = ingester.validate_manifest(case_dir)
    index_path = ingester.generate_case_index(
        case_dir,
        manifest_data=manifest_data,
        timestamp_mode=timestamp_mode,
    )
    index_payload = json.loads(index_path.read_text(encoding="utf-8"))
    report_path = _write_ingest_report(case_dir, index_payload)
    return {
        "integrity_status": str(index_payload.get("integrity", {}).get("status", "UNKNOWN")),
        "case_dir": str(case_dir),
        "case_index": str(index_path),
        "ingest_report": str(report_path),
    }
