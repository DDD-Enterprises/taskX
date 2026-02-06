"""Case bundle ingestion with deterministic integrity indexing."""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from taskx.schemas.validator import validate_data
from taskx.utils.schema_registry import SchemaRegistry

DETERMINISTIC_TIMESTAMP = "1970-01-01T00:00:00Z"


def _sha256_file(path: Path) -> str:
    """Compute SHA256 for a single file path."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_extract(zip_path: Path, dest: Path) -> None:
    """Extract zip into dest while blocking traversal and symlink entries."""
    dest.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as archive:
        for info in sorted(archive.infolist(), key=lambda item: item.filename):
            member = Path(info.filename)
            if member.is_absolute() or ".." in member.parts:
                raise ValueError(f"Unsafe zip entry path: {info.filename}")

            file_mode = (info.external_attr >> 16) & 0o170000
            if file_mode == 0o120000:
                raise ValueError(f"Symlink entries are not allowed: {info.filename}")

            target = dest / member
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue

            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info, "r") as source, target.open("wb") as out_file:
                shutil.copyfileobj(source, out_file)


def _classify_path(rel_path: str) -> str:
    """Classify file categories for CASE_INDEX entries."""
    normalized = rel_path.replace("\\", "/")
    if normalized == "taskx/task_queue.json":
        return "taskx_task_queue"
    if normalized.startswith("taskx/packets/") or (
        normalized.startswith("taskx/runs/") and normalized.endswith("/TASK_PACKET.md")
    ):
        return "taskx_packet"
    if normalized.startswith("taskx/runs/"):
        return "taskx_run_artifact"
    if normalized == "repo/REPO_SNAPSHOT.json":
        return "repo_snapshot"
    if normalized.startswith("repo/logs/") or normalized == "repo/LOG_INDEX.json":
        return "repo_log"
    if normalized.startswith("reports/"):
        return "report"
    return "unknown"


def _build_case_index(case_root: Path) -> dict[str, Any]:
    """Build deterministic file index for all extracted bundle files."""
    files: list[dict[str, Any]] = []
    run_ids: set[str] = set()

    for path in sorted(p for p in case_root.rglob("*") if p.is_file()):
        rel = path.relative_to(case_root).as_posix()
        category = _classify_path(rel)

        parts = rel.split("/")
        if len(parts) >= 3 and parts[0] == "taskx" and parts[1] == "runs":
            run_ids.add(parts[2])

        files.append(
            {
                "path": rel,
                "sha256": _sha256_file(path),
                "size_bytes": path.stat().st_size,
                "category": category,
            }
        )

    counts = {
        "files_total": len(files),
        "run_dirs": len(run_ids),
        "packets": sum(1 for item in files if item["category"] == "taskx_packet"),
    }
    return {"files": files, "counts": counts}


def _timestamp(timestamp_mode: str) -> str:
    if timestamp_mode == "deterministic":
        return DETERMINISTIC_TIMESTAMP
    if timestamp_mode == "wallclock":
        return datetime.now(UTC).isoformat()
    raise ValueError(f"Invalid timestamp_mode: {timestamp_mode}")


def _atomic_write_text(path: Path, content: str) -> None:
    """Write file atomically in target directory."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        delete=False,
        prefix=f".{path.name}.",
    ) as handle:
        handle.write(content)
        temp_path = Path(handle.name)

    temp_path.replace(path)


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)
    if not isinstance(raw, dict):
        raise ValueError(f"Expected object JSON at {path}")
    return raw


def _build_integrity(
    *, manifest: dict[str, Any], actual_files: list[dict[str, Any]], schema_errors: list[str]
) -> dict[str, Any]:
    """Compare manifest file entries to extracted index entries."""
    mismatches: list[dict[str, Any]] = []

    if schema_errors:
        mismatches.extend(
            {
                "code": "schema_validation_failed",
                "path": "case/CASE_MANIFEST.json",
                "message": error,
            }
            for error in sorted(schema_errors)
        )

    actual_by_path = {item["path"]: item for item in actual_files}
    expected_files = manifest.get("files")

    if not isinstance(expected_files, list):
        mismatches.append(
            {
                "code": "manifest_files_missing",
                "path": "case/CASE_MANIFEST.json",
                "message": "CASE_MANIFEST.json is missing files[] for integrity checks",
            }
        )
        return {
            "status": "failed",
            "mismatches_count": len(mismatches),
            "mismatches": mismatches,
        }

    expected_paths: set[str] = set()

    for idx, expected in enumerate(expected_files):
        if not isinstance(expected, dict):
            mismatches.append(
                {
                    "code": "manifest_entry_invalid",
                    "path": f"case/CASE_MANIFEST.json#files[{idx}]",
                    "message": "Manifest file entry must be an object",
                }
            )
            continue

        path = expected.get("path")
        sha = expected.get("sha256")
        size = expected.get("size_bytes")

        if not isinstance(path, str):
            mismatches.append(
                {
                    "code": "manifest_entry_missing_path",
                    "path": f"case/CASE_MANIFEST.json#files[{idx}]",
                    "message": "Manifest file entry missing path",
                }
            )
            continue

        expected_paths.add(path)
        actual = actual_by_path.get(path)
        if actual is None:
            mismatches.append(
                {
                    "code": "missing_file",
                    "path": path,
                    "expected_sha256": sha,
                    "expected_size_bytes": size,
                }
            )
            continue

        if isinstance(sha, str) and actual["sha256"] != sha:
            mismatches.append(
                {
                    "code": "sha256_mismatch",
                    "path": path,
                    "expected_sha256": sha,
                    "actual_sha256": actual["sha256"],
                }
            )

        if isinstance(size, int) and actual["size_bytes"] != size:
            mismatches.append(
                {
                    "code": "size_mismatch",
                    "path": path,
                    "expected_size_bytes": size,
                    "actual_size_bytes": actual["size_bytes"],
                }
            )

    ignored_unexpected = {"case/CASE_MANIFEST.json"}
    for unexpected_path in sorted(set(actual_by_path) - expected_paths - ignored_unexpected):
        mismatches.append(
            {
                "code": "unexpected_file",
                "path": unexpected_path,
                "actual_sha256": actual_by_path[unexpected_path]["sha256"],
                "actual_size_bytes": actual_by_path[unexpected_path]["size_bytes"],
            }
        )

    status = "passed" if not mismatches else "failed"
    return {
        "status": status,
        "mismatches_count": len(mismatches),
        "mismatches": mismatches,
    }


def _compute_counts(case_root: Path, files: list[dict[str, Any]], base_counts: dict[str, int]) -> dict[str, int]:
    """Compute CASE_INDEX summary counters."""
    logs_included = 0
    logs_skipped = 0

    log_index_path = case_root / "repo" / "LOG_INDEX.json"
    if log_index_path.exists():
        try:
            log_index = _load_json(log_index_path)
            included = log_index.get("included", [])
            skipped = log_index.get("skipped", [])
            if isinstance(included, list):
                logs_included = len(included)
            if isinstance(skipped, list):
                logs_skipped = len(skipped)
        except Exception:
            logs_included = sum(1 for item in files if item["path"].startswith("repo/logs/"))
            logs_skipped = 0
    else:
        logs_included = sum(1 for item in files if item["path"].startswith("repo/logs/"))

    return {
        "files_total": base_counts["files_total"],
        "logs_included": logs_included,
        "logs_skipped": logs_skipped,
        "run_dirs": base_counts["run_dirs"],
        "packets": base_counts["packets"],
    }


def _render_ingest_report(case_index: dict[str, Any], manifest_schema_valid: bool) -> str:
    """Render deterministic markdown report for ingest output."""
    integrity = case_index["integrity"]
    counts = case_index["counts"]

    lines = [
        "# CASE Ingest Report",
        "",
        f"- case_id: `{case_index['case_id']}`",
        f"- ingested_at: `{case_index['ingested_at']}`",
        f"- zip_sha256: `{case_index['zip_sha256']}`",
        f"- manifest_schema_valid: `{str(manifest_schema_valid).lower()}`",
        f"- integrity_status: `{integrity['status']}`",
        f"- mismatches_count: `{integrity['mismatches_count']}`",
        "",
        "## Counts",
        "",
        f"- files_total: `{counts['files_total']}`",
        f"- logs_included: `{counts['logs_included']}`",
        f"- logs_skipped: `{counts['logs_skipped']}`",
        f"- run_dirs: `{counts['run_dirs']}`",
        f"- packets: `{counts['packets']}`",
        "",
        "## Integrity Mismatches",
        "",
    ]

    mismatches = integrity.get("mismatches", [])
    if mismatches:
        for mismatch in mismatches:
            code = mismatch.get("code", "unknown")
            path = mismatch.get("path", "")
            message = mismatch.get("message")
            detail = f"{code} :: {path}"
            if isinstance(message, str) and message:
                detail = f"{detail} :: {message}"
            lines.append(f"- `{detail}`")
    else:
        lines.append("- none")

    lines.append("")
    return "\n".join(lines)


def ingest_bundle(
    zip_path: Path,
    output_dir: Path,
    timestamp_mode: str = "deterministic",
) -> dict[str, str]:
    """Ingest a case bundle zip and emit CASE_INDEX/ingest report."""
    if timestamp_mode not in {"deterministic", "wallclock"}:
        raise ValueError(f"Invalid timestamp_mode: {timestamp_mode}")

    if not zip_path.exists() or not zip_path.is_file():
        raise ValueError(f"Zip does not exist or is not a file: {zip_path}")

    if not zipfile.is_zipfile(zip_path):
        raise ValueError(f"Zip is not readable: {zip_path}")

    zip_hash = _sha256_file(zip_path)

    with tempfile.TemporaryDirectory() as temp_dir:
        extracted_root = Path(temp_dir) / "extracted"
        _safe_extract(zip_path, extracted_root)

        manifest_path = extracted_root / "case" / "CASE_MANIFEST.json"
        if not manifest_path.exists():
            raise ValueError("Bundle missing required file: case/CASE_MANIFEST.json")

        manifest = _load_json(manifest_path)
        # Explicit registry lookup keeps behavior aligned with existing schema-loading contracts.
        SchemaRegistry().get_json("case_bundle")
        schema_valid, schema_errors = validate_data(manifest, "case_bundle", strict=False)

        manifest_case_id = manifest.get("case_id")
        if isinstance(manifest_case_id, str) and manifest_case_id.strip():
            case_id = manifest_case_id.strip()
        else:
            case_id = zip_path.stem

        output_dir.mkdir(parents=True, exist_ok=True)
        case_root = output_dir / case_id
        if case_root.exists():
            raise FileExistsError(f"Case output directory already exists: {case_root}")

        shutil.copytree(extracted_root, case_root)

    built = _build_case_index(case_root)
    files = built["files"]
    integrity = _build_integrity(manifest=manifest, actual_files=files, schema_errors=schema_errors)
    counts = _compute_counts(case_root, files, built["counts"])

    case_index = {
        "schema_version": "1.0",
        "case_id": case_id,
        "ingested_at": _timestamp(timestamp_mode),
        "zip_sha256": zip_hash,
        "integrity": integrity,
        "counts": counts,
        "files": files,
    }

    case_index_path = case_root / "CASE_INDEX.json"
    _atomic_write_text(case_index_path, json.dumps(case_index, indent=2, ensure_ascii=False))

    report = _render_ingest_report(case_index, manifest_schema_valid=schema_valid)
    report_path = case_root / "CASE_INGEST_REPORT.md"
    _atomic_write_text(report_path, report)

    return {
        "case_dir": str(case_root),
        "case_index": str(case_index_path),
        "ingest_report": str(report_path),
        "integrity_status": integrity["status"],
    }
