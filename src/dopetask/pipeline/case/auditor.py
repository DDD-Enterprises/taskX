"""Deterministic case audit for ingested dopeTask bundles."""

from __future__ import annotations

import json
import tempfile
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

DETERMINISTIC_TIMESTAMP = "1970-01-01T00:00:00Z"
REQUIRED_RUN_FILES = [
    "PLAN.md",
    "CHECKLIST.md",
    "RUNLOG.md",
    "EVIDENCE.md",
    "COMMANDS.sh",
    "RUN_ENVELOPE.json",
    "RUN_SUMMARY.json",
]
CLAIM_TYPES = [
    "change_made",
    "test_passed",
    "test_failed",
    "constraint_respected",
    "unknown",
]


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


def _discover_runs(case_dir: Path) -> list[Path]:
    """Discover run directories under dopetask/runs."""
    runs_root = case_dir / "dopetask" / "runs"
    if not runs_root.exists():
        return []
    return sorted([entry for entry in runs_root.iterdir() if entry.is_dir()], key=lambda item: item.name)


def _load_run_summary(run_dir: Path) -> dict[str, Any]:
    """Load run summary, returning a minimal fallback when unavailable."""
    summary_path = run_dir / "RUN_SUMMARY.json"
    if not summary_path.exists():
        return {"run_id": run_dir.name, "_summary_missing": True}

    try:
        data = _load_json(summary_path)
    except Exception:
        return {"run_id": run_dir.name, "_summary_missing": True}

    data.setdefault("run_id", run_dir.name)
    data["_summary_missing"] = False
    return data


def _aggregate_anomalies(run_summaries: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate anomaly strings and per-run occurrences."""
    anomaly_map: dict[str, set[str]] = {}

    for summary in run_summaries:
        run_id = str(summary.get("run_id", "UNKNOWN"))
        status = summary.get("status", {})
        if not isinstance(status, dict):
            continue

        anomalies = status.get("anomalies", [])
        if not isinstance(anomalies, list):
            continue

        for anomaly in anomalies:
            if not isinstance(anomaly, str):
                continue
            anomaly_map.setdefault(anomaly, set()).add(run_id)

    top = [
        {
            "text": text,
            "count": len(run_ids),
            "run_ids": sorted(run_ids),
        }
        for text, run_ids in anomaly_map.items()
    ]
    top.sort(key=lambda item: (-cast("int", item["count"]), cast("str", item["text"])))

    return {
        "total_unique": len(top),
        "top": top[:10],
    }


def _aggregate_claims(run_summaries: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate claims by type and recurring textual signatures."""
    counts = dict.fromkeys(CLAIM_TYPES, 0)
    failed_map: dict[str, set[str]] = {}
    unknown_map: dict[str, set[str]] = {}

    for summary in run_summaries:
        run_id = str(summary.get("run_id", "UNKNOWN"))
        claims = summary.get("claims", {})
        if not isinstance(claims, dict):
            continue

        items = claims.get("items", [])
        if not isinstance(items, list):
            continue

        for item in items:
            if not isinstance(item, dict):
                continue

            claim_type = item.get("claim_type")
            text = item.get("text")

            if isinstance(claim_type, str) and claim_type in counts:
                counts[claim_type] += 1
            else:
                counts["unknown"] += 1

            if not isinstance(text, str) or not text:
                continue

            if claim_type == "test_failed":
                failed_map.setdefault(text, set()).add(run_id)
            if claim_type == "unknown":
                unknown_map.setdefault(text, set()).add(run_id)

    top_failed = [
        {
            "text": text,
            "count": len(run_ids),
            "run_ids": sorted(run_ids),
        }
        for text, run_ids in failed_map.items()
        if len(run_ids) >= 1
    ]
    top_failed.sort(key=lambda item: (-cast("int", item["count"]), cast("str", item["text"])))

    repeated_unknown = [
        {
            "text": text,
            "count": len(run_ids),
            "run_ids": sorted(run_ids),
        }
        for text, run_ids in unknown_map.items()
        if len(run_ids) > 1
    ]
    repeated_unknown.sort(key=lambda item: (-cast("int", item["count"]), cast("str", item["text"])))

    return {
        "claim_counts_by_type": counts,
        "top_recurring_test_failed": top_failed[:10],
        "repeated_unknown_claims": repeated_unknown[:10],
    }


def _detect_verification_gaps(run_summaries: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute verification hygiene metrics from run summaries."""
    total = len(run_summaries)
    checklist_false = 0
    commands_false = 0
    outputs_false = 0

    for summary in run_summaries:
        status = summary.get("status", {})
        if not isinstance(status, dict):
            checklist_false += 1
            commands_false += 1
            outputs_false += 1
            continue

        if not bool(status.get("checklist_completed", False)):
            checklist_false += 1
        if not bool(status.get("verification_commands_listed", False)):
            commands_false += 1
        if not bool(status.get("verification_outputs_present", False)):
            outputs_false += 1

    if total == 0:
        return {
            "runs_with_summaries": 0,
            "pct_checklist_incomplete": 0.0,
            "pct_verification_commands_missing": 0.0,
            "pct_verification_outputs_missing": 0.0,
            "top_anomalies": [],
        }

    anomaly_top = _aggregate_anomalies(run_summaries)["top"]
    top_anomalies = [entry["text"] for entry in anomaly_top]

    return {
        "runs_with_summaries": total,
        "pct_checklist_incomplete": round((checklist_false / total) * 100.0, 2),
        "pct_verification_commands_missing": round((commands_false / total) * 100.0, 2),
        "pct_verification_outputs_missing": round((outputs_false / total) * 100.0, 2),
        "top_anomalies": top_anomalies,
    }


def _extract_path_strings(data: Any) -> list[str]:
    """Recursively pull likely file path strings from arbitrary JSON-like data."""
    found: list[str] = []

    if isinstance(data, dict):
        for key, value in data.items():
            if key in {"path", "file", "filepath"} and isinstance(value, str):
                found.append(value)
            else:
                found.extend(_extract_path_strings(value))
    elif isinstance(data, list):
        for item in data:
            found.extend(_extract_path_strings(item))

    return found


def _compute_drift_indicators(case_dir: Path, run_dirs: list[Path], run_summaries: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute drift and consistency indicators across runs."""
    missing_by_run: list[dict[str, Any]] = []
    missing_counts: Counter[str] = Counter()

    for run_dir in run_dirs:
        missing = [name for name in REQUIRED_RUN_FILES if not (run_dir / name).exists()]
        if missing:
            missing_by_run.append({"run_id": run_dir.name, "missing_files": missing})
            for filename in missing:
                missing_counts[filename] += 1

    timestamp_modes = sorted(
        {
            str(summary.get("timestamp_mode"))
            for summary in run_summaries
            if isinstance(summary.get("timestamp_mode"), str)
        }
    )

    diff_paths = sorted((case_dir / "dopetask" / "runs").glob("*/ALLOWLIST_DIFF.json"))
    hot_paths: dict[str, Any]
    if not diff_paths:
        hot_paths = {
            "status": "UNKNOWN",
            "reason": "ALLOWLIST_DIFF.json not present in bundle",
            "top_paths": [],
        }
    else:
        counter: Counter[str] = Counter()
        for diff_path in diff_paths:
            try:
                payload = _load_json(diff_path)
            except Exception:
                continue
            for path in _extract_path_strings(payload):
                counter[path] += 1

        if not counter:
            hot_paths = {
                "status": "UNKNOWN",
                "reason": "ALLOWLIST_DIFF.json did not contain parseable path fields",
                "top_paths": [],
            }
        else:
            top_paths = [
                {"path": path, "count": count}
                for path, count in counter.most_common(10)
            ]
            hot_paths = {
                "status": "available",
                "reason": "derived from ALLOWLIST_DIFF.json",
                "top_paths": top_paths,
            }

    return {
        "missing_required_files": {
            "required": REQUIRED_RUN_FILES,
            "missing_by_run": missing_by_run,
            "missing_counts": dict(sorted(missing_counts.items())),
        },
        "timestamp_mode": {
            "values": timestamp_modes,
            "inconsistent": len(timestamp_modes) > 1,
        },
        "hot_paths": hot_paths,
    }


def _compute_log_capture_health(case_dir: Path) -> dict[str, Any]:
    """Summarize log capture inclusion and skip behavior."""
    log_index_path = case_dir / "repo" / "LOG_INDEX.json"
    if not log_index_path.exists():
        return {
            "included_count": 0,
            "skipped_count": 0,
            "skip_reasons_histogram": {},
            "top_skipped_by_size": [],
            "status": "UNKNOWN",
            "reason": "repo/LOG_INDEX.json missing",
        }

    payload = _load_json(log_index_path)
    included = payload.get("included", [])
    skipped = payload.get("skipped", [])
    included_entries = included if isinstance(included, list) else []
    skipped_entries = skipped if isinstance(skipped, list) else []

    reason_counter: Counter[str] = Counter()
    skipped_with_size: list[dict[str, Any]] = []

    for item in skipped_entries:
        if not isinstance(item, dict):
            continue
        reason = item.get("reason")
        if isinstance(reason, str):
            reason_counter[reason] += 1

        size = item.get("size")
        if not isinstance(size, int):
            size = item.get("size_bytes")
        if isinstance(size, int):
            skipped_with_size.append(
                {
                    "path": item.get("path", "UNKNOWN"),
                    "size": size,
                    "reason": reason,
                }
            )

    skipped_with_size.sort(key=lambda entry: (-entry["size"], str(entry["path"])))

    return {
        "included_count": len(included_entries),
        "skipped_count": len(skipped_entries),
        "skip_reasons_histogram": dict(sorted(reason_counter.items())),
        "top_skipped_by_size": skipped_with_size[:10],
        "status": "available",
        "reason": "repo/LOG_INDEX.json",
    }


def _emit_findings_json(output_dir: Path, findings: dict[str, Any]) -> Path:
    """Write CASE_FINDINGS.json."""
    path = output_dir / "CASE_FINDINGS.json"
    _atomic_write_text(path, json.dumps(findings, indent=2, ensure_ascii=False))
    return path


def _emit_report_md(output_dir: Path, findings: dict[str, Any]) -> Path:
    """Write human-readable CASE_AUDIT_REPORT.md."""
    run_coverage = findings["run_coverage"]
    failures = findings["failure_signatures"]
    verification = findings["verification_hygiene"]

    lines = [
        "# CASE Audit Report",
        "",
        f"- case_id: `{findings['case_id']}`",
        f"- generated_at: `{findings['generated_at']}`",
        f"- integrity_status: `{findings['integrity']['status']}`",
        "",
        "## Run Coverage",
        "",
        f"- runs_found: `{run_coverage['runs_found']}`",
        f"- run_summaries_found: `{run_coverage['run_summaries_found']}`",
    ]

    if run_coverage["runs_found"] == 0:
        lines.append("- 0 runs found")

    if run_coverage["missing_summaries"]:
        lines.append(f"- missing_summaries: `{', '.join(run_coverage['missing_summaries'])}`")

    lines.extend(
        [
            "",
            "## Verification Hygiene",
            "",
            f"- pct_checklist_incomplete: `{verification['pct_checklist_incomplete']}`",
            f"- pct_verification_commands_missing: `{verification['pct_verification_commands_missing']}`",
            f"- pct_verification_outputs_missing: `{verification['pct_verification_outputs_missing']}`",
            "",
            "## Recurring Test Failures",
            "",
        ]
    )

    recurring = failures.get("top_recurring_test_failed", [])
    if recurring:
        for entry in recurring:
            lines.append(
                f"- `{entry['text']}` :: count={entry['count']} :: runs={','.join(entry['run_ids'])}"
            )
    else:
        lines.append("- none")

    report_path = output_dir / "CASE_AUDIT_REPORT.md"
    _atomic_write_text(report_path, "\n".join(lines) + "\n")
    return report_path


def _build_recommendations(
    *,
    case_dir: Path,
    findings: dict[str, Any],
) -> list[dict[str, Any]]:
    """Create deterministic recommendation list from findings."""
    recommendations: list[dict[str, Any]] = []

    integrity = findings["integrity"]
    run_coverage = findings["run_coverage"]
    verification = findings["verification_hygiene"]
    failures = findings["failure_signatures"]
    drift = findings["drift_indicators"]

    if integrity["status"] != "passed":
        recommendations.append(
            {
                "title": "Repair case integrity before diagnosis",
                "rationale": (
                    f"Integrity status is {integrity['status']} with "
                    f"{integrity['mismatches_count']} mismatches."
                ),
                "evidence_pointers": [str(case_dir / "CASE_INDEX.json")],
                "suggested_next_packet_type": "run_artifact_consistency",
                "acceptance_criteria": [
                    "Bundle re-ingests with integrity.status == passed",
                    "CASE_MANIFEST.json files[] matches extracted content",
                ],
            }
        )

    if run_coverage["run_summaries_found"] == 0:
        recommendations.append(
            {
                "title": "Acquire summaries for cross-run evidence",
                "rationale": (
                    "UNKNOWN: No RUN_SUMMARY.json artifacts were found. "
                    "Request a new bundle containing dopetask/runs/*/RUN_SUMMARY.json."
                ),
                "evidence_pointers": [str(case_dir / "dopetask" / "runs")],
                "suggested_next_packet_type": "verification_hardening",
                "acceptance_criteria": [
                    "At least one run includes RUN_SUMMARY.json",
                    "Audit can compute verification hygiene from summaries",
                ],
            }
        )

    if (
        verification["pct_checklist_incomplete"] > 0
        or verification["pct_verification_commands_missing"] > 0
        or verification["pct_verification_outputs_missing"] > 0
    ):
        recommendations.append(
            {
                "title": "Harden verification completion discipline",
                "rationale": (
                    "One or more runs lacked checklist completion, verification commands, "
                    "or verification outputs."
                ),
                "evidence_pointers": [str(case_dir / "CASE_INDEX.json")],
                "suggested_next_packet_type": "verification_hardening",
                "acceptance_criteria": [
                    "All runs set checklist_completed == true",
                    "All runs set verification_commands_listed == true",
                    "All runs set verification_outputs_present == true",
                ],
            }
        )

    if failures["top_recurring_test_failed"]:
        recommendations.append(
            {
                "title": "Isolate recurring failure signatures",
                "rationale": "Repeated test_failed claim texts indicate likely flakiness or shared root causes.",
                "evidence_pointers": [str(case_dir / "CASE_INDEX.json")],
                "suggested_next_packet_type": "flakiness_isolation",
                "acceptance_criteria": [
                    "Top recurring test_failed signatures have targeted reproductions",
                    "Failure recurrence count decreases across new runs",
                ],
            }
        )

    hot_paths = drift["hot_paths"]
    if hot_paths.get("status") == "available" and hot_paths.get("top_paths"):
        recommendations.append(
            {
                "title": "Tighten allowlist around hot paths",
                "rationale": "Hot paths from ALLOWLIST_DIFF.json suggest concentrated churn.",
                "evidence_pointers": [str(case_dir / "dopetask" / "runs")],
                "suggested_next_packet_type": "allowlist_tightening",
                "acceptance_criteria": [
                    "Allowlist patterns explicitly cover high-churn files",
                    "Future runs avoid out-of-scope file touch events",
                ],
            }
        )
    elif hot_paths.get("status") == "UNKNOWN":
        recommendations.append(
            {
                "title": "Collect allowlist drift evidence",
                "rationale": (
                    "UNKNOWN: ALLOWLIST_DIFF evidence is missing or unparseable. "
                    "Request a new bundle with ALLOWLIST_DIFF.json per run."
                ),
                "evidence_pointers": [str(case_dir / "dopetask" / "runs")],
                "suggested_next_packet_type": "allowlist_tightening",
                "acceptance_criteria": [
                    "ALLOWLIST_DIFF.json exists for audited runs",
                    "Hot paths can be computed deterministically",
                ],
            }
        )

    if not recommendations:
        recommendations.append(
            {
                "title": "No critical issues detected",
                "rationale": "Audit found no deterministic triggers for packet recommendations.",
                "evidence_pointers": [str(case_dir / "CASE_INDEX.json")],
                "suggested_next_packet_type": "run_artifact_consistency",
                "acceptance_criteria": ["Maintain current evidence and integrity posture"],
            }
        )

    for idx, recommendation in enumerate(recommendations, start=1):
        recommendation["id"] = f"REC-{idx:04d}"

    return recommendations


def _emit_packet_recommendations_json(
    output_dir: Path,
    *,
    case_dir: Path,
    case_id: str,
    generated_at: str,
    findings: dict[str, Any],
) -> Path:
    """Write PACKET_RECOMMENDATIONS.json."""
    payload = {
        "schema_version": "1.0",
        "case_id": case_id,
        "generated_at": generated_at,
        "recommendations": _build_recommendations(case_dir=case_dir, findings=findings),
    }
    path = output_dir / "PACKET_RECOMMENDATIONS.json"
    _atomic_write_text(path, json.dumps(payload, indent=2, ensure_ascii=False))
    return path


def audit_case(
    case_dir: Path,
    output_dir: Path,
    timestamp_mode: str = "deterministic",
) -> dict[str, str]:
    """Audit an ingested case directory and emit deterministic findings and reports."""
    if timestamp_mode not in {"deterministic", "wallclock"}:
        raise ValueError(f"Invalid timestamp_mode: {timestamp_mode}")

    if not case_dir.exists() or not case_dir.is_dir():
        raise ValueError(f"Case directory not found: {case_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    case_index_path = case_dir / "CASE_INDEX.json"
    if case_index_path.exists():
        case_index = _load_json(case_index_path)
        case_id = str(case_index.get("case_id", case_dir.name))
        integrity = case_index.get("integrity", {"status": "UNKNOWN", "mismatches": []})
        if not isinstance(integrity, dict):
            integrity = {"status": "UNKNOWN", "mismatches": []}
    else:
        case_index = {}
        case_id = case_dir.name
        integrity = {
            "status": "UNKNOWN",
            "mismatches_count": 0,
            "mismatches": [
                {
                    "code": "case_index_missing",
                    "path": "CASE_INDEX.json",
                    "message": "Ingest output missing; request a fresh ingest run.",
                }
            ],
        }

    integrity.setdefault("status", "UNKNOWN")
    integrity.setdefault("mismatches", [])
    integrity.setdefault("mismatches_count", len(integrity.get("mismatches", [])))

    run_dirs = _discover_runs(case_dir)
    run_summaries_all = [_load_run_summary(run_dir) for run_dir in run_dirs]
    run_summaries = [summary for summary in run_summaries_all if not summary.get("_summary_missing")]

    missing_summaries = sorted(
        run_dir.name
        for run_dir, summary in zip(run_dirs, run_summaries_all, strict=False)
        if summary.get("_summary_missing")
    )

    anomalies = _aggregate_anomalies(run_summaries)
    claims = _aggregate_claims(run_summaries)
    verification_hygiene = _detect_verification_gaps(run_summaries)
    drift_indicators = _compute_drift_indicators(case_dir, run_dirs, run_summaries)
    log_capture_health = _compute_log_capture_health(case_dir)

    findings = {
        "schema_version": "1.0",
        "case_id": case_id,
        "generated_at": _timestamp(timestamp_mode),
        "timestamp_mode": timestamp_mode,
        "integrity": {
            "status": integrity["status"],
            "mismatches_count": integrity["mismatches_count"],
            "mismatches": integrity["mismatches"],
        },
        "run_coverage": {
            "runs_found": len(run_dirs),
            "run_summaries_found": len(run_summaries),
            "missing_summaries": missing_summaries,
        },
        "verification_hygiene": verification_hygiene,
        "failure_signatures": {
            "anomalies": anomalies,
            **claims,
        },
        "drift_indicators": drift_indicators,
        "log_capture_health": log_capture_health,
    }

    findings_path = _emit_findings_json(output_dir, findings)
    report_path = _emit_report_md(output_dir, findings)
    recommendations_path = _emit_packet_recommendations_json(
        output_dir,
        case_dir=case_dir,
        case_id=case_id,
        generated_at=str(findings["generated_at"]),
        findings=findings,
    )

    return {
        "findings": str(findings_path),
        "report": str(report_path),
        "recommendations": str(recommendations_path),
    }
