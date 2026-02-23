"""Project readiness doctor for TaskX/ChatX directive workflows."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from dopetask.project.common import (
    DISABLED_TEXT,
    MANAGED_FILES,
    MANAGED_TEMPLATE_FILES,
    PACK_ORDER,
    SENTINELS,
    read_pack_text,
    read_template_text,
)
from dopetask.project.mode import MODE_TO_PACK_ENABLED, VALID_MODES, normalize_mode, set_mode

if TYPE_CHECKING:
    from pathlib import Path

SUPERVISOR_PROMPT_FILENAME = "SUPERVISOR_PRIMING_PROMPT.txt"


def check_project(project_dir: Path) -> dict[str, Any]:
    """Validate project readiness without mutating managed project files."""
    files = _managed_files(project_dir)
    checks: list[dict[str, Any]] = []

    missing_files = [name for name, path in files.items() if not path.exists()]
    checks.append(
        {
            "id": "files_present",
            "status": "pass" if not missing_files else "fail",
            "message": "All required project instruction files are present"
            if not missing_files
            else f"Missing required files: {', '.join(missing_files)}",
            "files": missing_files,
        }
    )

    sentinel_issues: dict[str, list[str]] = {}
    per_file_status: dict[str, dict[str, str]] = {}
    for filename, file_path in files.items():
        if not file_path.exists():
            continue
        analysis = _analyze_instruction_file(file_path)
        per_file_status[filename] = analysis["pack_status"]
        if analysis["issues"]:
            sentinel_issues[filename] = analysis["issues"]

    if sentinel_issues:
        issue_lines = [
            f"{filename}: {'; '.join(issues)}"
            for filename, issues in sorted(sentinel_issues.items())
        ]
        checks.append(
            {
                "id": "sentinel_integrity",
                "status": "fail",
                "message": "Sentinel issues detected: " + " | ".join(issue_lines),
                "files": sorted(sentinel_issues),
            }
        )
    else:
        checks.append(
            {
                "id": "sentinel_integrity",
                "status": "pass",
                "message": "TaskX/ChatX sentinel blocks are present and well-formed",
                "files": sorted(per_file_status),
            }
        )

    detected_mode = _detect_mode(per_file_status)
    if detected_mode == "inconsistent":
        drift_files = _find_drift_files(per_file_status)
        checks.append(
            {
                "id": "pack_status_consistency",
                "status": "fail",
                "message": "Pack status differs between files",
                "files": drift_files,
            }
        )
    elif detected_mode == "unknown":
        checks.append(
            {
                "id": "pack_status_consistency",
                "status": "fail",
                "message": "Pack status could not be determined from current files",
                "files": sorted(per_file_status),
            }
        )
    else:
        checks.append(
            {
                "id": "pack_status_consistency",
                "status": "pass",
                "message": f"Pack status is consistent (mode={detected_mode})",
                "files": sorted(per_file_status),
            }
        )

    checks.append(_check_supervisor_prompt(project_dir, detected_mode))

    overall_status = "pass" if all(item["status"] == "pass" for item in checks) else "fail"
    return {
        "status": overall_status,
        "checks": checks,
        "detected_mode": detected_mode,
        "per_file_status": per_file_status,
    }


def fix_project(project_dir: Path, mode: str | None) -> dict[str, Any]:
    """Repair common project readiness issues and return post-fix doctor report."""
    project_dir.mkdir(parents=True, exist_ok=True)
    actions_taken: list[str] = []

    for filename in MANAGED_FILES:
        target = project_dir / filename
        if target.exists():
            continue
        template_name = MANAGED_TEMPLATE_FILES[filename]
        target.write_text(read_template_text(template_name), encoding="utf-8")
        actions_taken.append(f"created:{filename}")

    for filename in MANAGED_FILES:
        target = project_dir / filename
        if not target.exists():
            continue
        updated_text, changed = _insert_missing_sentinels(target.read_text(encoding="utf-8"))
        if changed:
            target.write_text(updated_text, encoding="utf-8")
            actions_taken.append(f"sentinels_repaired:{filename}")

    pre_fix_report = check_project(project_dir)
    target_mode = _resolve_fix_mode(pre_fix_report.get("detected_mode", "unknown"), mode)

    mode_result = set_mode(project_dir, target_mode)
    actions_taken.append(f"mode_applied:{target_mode}")
    actions_taken.extend(f"mode_changed:{name}" for name in mode_result["changed_files"])

    prompt_path = write_supervisor_prompt(project_dir, target_mode)
    actions_taken.append(f"supervisor_prompt_generated:{prompt_path.name}")

    report = check_project(project_dir)
    report["actions_taken"] = actions_taken
    report["applied_mode"] = target_mode
    return report


def write_supervisor_prompt(project_dir: Path, mode: str) -> Path:
    """Render generated/SUPERVISOR_PRIMING_PROMPT.txt for the given mode."""
    normalized_mode = normalize_mode(mode)
    generated_dir = project_dir / "generated"
    generated_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = generated_dir / SUPERVISOR_PROMPT_FILENAME
    prompt_path.write_text(_render_supervisor_prompt(normalized_mode), encoding="utf-8")
    return prompt_path


def write_doctor_reports(project_dir: Path, report: dict[str, Any]) -> dict[str, str]:
    """Persist doctor report as markdown and JSON under generated/."""
    generated_dir = project_dir / "generated"
    generated_dir.mkdir(parents=True, exist_ok=True)

    md_path = generated_dir / "PROJECT_DOCTOR_REPORT.md"
    json_path = generated_dir / "PROJECT_DOCTOR_REPORT.json"

    md_path.write_text(_render_doctor_markdown(project_dir, report), encoding="utf-8")
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    return {"markdown": str(md_path), "json": str(json_path)}


def render_doctor_summary(report: dict[str, Any]) -> str:
    """Render a short table-like summary for CLI output."""
    lines = [
        "PROJECT DOCTOR",
        f"status={report['status']} detected_mode={report.get('detected_mode', 'unknown')}",
        "",
        "checks:",
    ]
    for check in report.get("checks", []):
        lines.append(f"- [{check['status'].upper()}] {check['id']}: {check['message']}")
    return "\n".join(lines)


def _managed_files(project_dir: Path) -> dict[str, Path]:
    return {filename: project_dir / filename for filename in MANAGED_FILES}


def _analyze_instruction_file(file_path: Path) -> dict[str, Any]:
    text = file_path.read_text(encoding="utf-8")
    issues: list[str] = []
    pack_status: dict[str, str] = {}

    for pack_name in PACK_ORDER:
        begin_marker, end_marker = SENTINELS[pack_name]
        begin_count = text.count(begin_marker)
        end_count = text.count(end_marker)

        if begin_count == 0 or end_count == 0:
            if begin_count == 0:
                issues.append(f"missing {pack_name} begin sentinel")
            if end_count == 0:
                issues.append(f"missing {pack_name} end sentinel")
            pack_status[pack_name] = "unknown"
            continue

        if begin_count > 1 or end_count > 1:
            issues.append(f"duplicate {pack_name} sentinels")
            pack_status[pack_name] = "unknown"
            continue

        begin_index = text.find(begin_marker)
        end_index = text.find(end_marker)
        if end_index < begin_index:
            issues.append(f"misordered {pack_name} sentinels")
            pack_status[pack_name] = "unknown"
            continue

        content_start = begin_index + len(begin_marker)
        block_content = text[content_start:end_index].strip()
        if not block_content or block_content == DISABLED_TEXT:
            pack_status[pack_name] = "disabled"
        else:
            pack_status[pack_name] = "enabled"

    return {"issues": issues, "pack_status": pack_status}


def _detect_mode(per_file_status: dict[str, dict[str, str]]) -> str:
    if not per_file_status:
        return "unknown"

    observed: set[tuple[bool, bool]] = set()
    for states in per_file_status.values():
        taskx_state = states.get("taskx")
        chatx_state = states.get("chatx")
        if taskx_state not in {"enabled", "disabled"}:
            return "unknown"
        if chatx_state not in {"enabled", "disabled"}:
            return "unknown"
        observed.add((taskx_state == "enabled", chatx_state == "enabled"))

    if len(observed) > 1:
        return "inconsistent"

    mapping = {
        (True, False): "taskx",
        (False, True): "chatx",
        (True, True): "both",
        (False, False): "none",
    }
    return mapping[next(iter(observed))]


def _find_drift_files(per_file_status: dict[str, dict[str, str]]) -> list[str]:
    signatures: dict[str, tuple[str, str]] = {}
    counts: dict[tuple[str, str], int] = {}

    for filename, states in per_file_status.items():
        signature = (states.get("taskx", "unknown"), states.get("chatx", "unknown"))
        signatures[filename] = signature
        counts[signature] = counts.get(signature, 0) + 1

    if not counts:
        return []

    baseline = max(counts.items(), key=lambda item: item[1])[0]
    drift = [filename for filename, signature in signatures.items() if signature != baseline]
    return sorted(drift)


def _check_supervisor_prompt(project_dir: Path, detected_mode: str) -> dict[str, Any]:
    prompt_path = project_dir / "generated" / SUPERVISOR_PROMPT_FILENAME
    if not prompt_path.exists():
        return {
            "id": "supervisor_prompt",
            "status": "fail",
            "message": "generated/SUPERVISOR_PRIMING_PROMPT.txt is missing",
            "files": [str(prompt_path)],
        }

    if detected_mode not in VALID_MODES:
        return {
            "id": "supervisor_prompt",
            "status": "fail",
            "message": "Cannot validate supervisor prompt while mode is unknown/inconsistent",
            "files": [str(prompt_path)],
        }

    actual = prompt_path.read_text(encoding="utf-8")
    expected = _render_supervisor_prompt(detected_mode)
    if actual != expected:
        return {
            "id": "supervisor_prompt",
            "status": "fail",
            "message": f"Supervisor prompt does not match expected mode '{detected_mode}'",
            "files": [str(prompt_path)],
        }

    return {
        "id": "supervisor_prompt",
        "status": "pass",
        "message": f"Supervisor prompt matches mode '{detected_mode}'",
        "files": [str(prompt_path)],
    }


def _render_supervisor_prompt(mode: str) -> str:
    mode_config = MODE_TO_PACK_ENABLED[mode]
    taskx_text = read_pack_text("taskx") if mode_config["taskx"] else DISABLED_TEXT
    chatx_text = read_pack_text("chatx") if mode_config["chatx"] else DISABLED_TEXT

    lines = [
        "# SUPERVISOR_PRIMING_PROMPT",
        "",
        "Generated by taskx project doctor/mode workflows.",
        f"mode: {mode}",
        "",
        "## TASKX",
        taskx_text,
        "",
        "## CHATX",
        chatx_text,
        "",
    ]
    return "\n".join(lines)


def _resolve_fix_mode(detected_mode: str, requested_mode: str | None) -> str:
    if requested_mode is not None:
        return normalize_mode(requested_mode)
    if detected_mode in VALID_MODES:
        return detected_mode
    return "taskx"


def _insert_missing_sentinels(text: str) -> tuple[str, bool]:
    updated = text
    changed = False

    for pack_name in PACK_ORDER:
        begin_marker, end_marker = SENTINELS[pack_name]
        begin_count = updated.count(begin_marker)
        end_count = updated.count(end_marker)

        if begin_count == 1 and end_count == 1:
            begin_index = updated.find(begin_marker)
            end_index = updated.find(end_marker)
            if begin_index < end_index:
                continue

        if begin_count == 0 and end_count == 0:
            updated = _append_block(updated, begin_marker, end_marker, DISABLED_TEXT)
            changed = True
            continue

        if begin_count == 0 and end_count == 1:
            end_index = updated.find(end_marker)
            insertion = f"{begin_marker}\n{DISABLED_TEXT}\n"
            updated = f"{updated[:end_index]}{insertion}{updated[end_index:]}"
            changed = True
            continue

        if begin_count == 1 and end_count == 0:
            begin_index = updated.find(begin_marker) + len(begin_marker)
            insertion = f"\n{DISABLED_TEXT}\n{end_marker}"
            updated = f"{updated[:begin_index]}{insertion}{updated[begin_index:]}"
            changed = True

    if changed and not updated.endswith("\n"):
        updated = f"{updated}\n"

    return updated, changed


def _append_block(text: str, begin_marker: str, end_marker: str, payload: str) -> str:
    stripped = text.rstrip("\n")
    separator = "\n\n" if stripped else ""
    return f"{stripped}{separator}{begin_marker}\n{payload}\n{end_marker}\n"


def _render_doctor_markdown(project_dir: Path, report: dict[str, Any]) -> str:
    lines: list[str] = [
        "# PROJECT_DOCTOR_REPORT",
        "",
        f"- project_dir: {project_dir}",
        f"- status: {report['status']}",
        f"- detected_mode: {report.get('detected_mode', 'unknown')}",
        "",
        "## Checks",
        "",
    ]

    for check in report.get("checks", []):
        files = check.get("files") or []
        files_text = ", ".join(files) if files else "(none)"
        lines.append(f"- id: {check['id']}")
        lines.append(f"  - status: {check['status']}")
        lines.append(f"  - message: {check['message']}")
        lines.append(f"  - files: {files_text}")

    lines.extend(["", "## Per-file Status", ""])
    per_file_status = report.get("per_file_status", {})
    if per_file_status:
        for filename in sorted(per_file_status):
            states = per_file_status[filename]
            lines.append(
                f"- {filename}: taskx={states.get('taskx', 'unknown')} chatx={states.get('chatx', 'unknown')}"
            )
    else:
        lines.append("- (none)")

    actions_taken = report.get("actions_taken", [])
    if actions_taken:
        lines.extend(["", "## Actions Taken", ""])
        for action in actions_taken:
            lines.append(f"- {action}")

    lines.append("")
    return "\n".join(lines)
