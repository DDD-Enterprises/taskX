"""Master project mode toggle for dopeTask/ChatX directive packs."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any

from dopetask.project.common import MANAGED_FILES
from dopetask.project.toggles import disable_pack, enable_pack, project_status

VALID_MODES: tuple[str, ...] = ("dopetask", "chatx", "both", "none")
MODE_TO_PACK_ENABLED: dict[str, dict[str, bool]] = {
    "dopetask": {"dopetask": True, "chatx": False},
    "chatx": {"dopetask": False, "chatx": True},
    "both": {"dopetask": True, "chatx": True},
    "none": {"dopetask": False, "chatx": False},
}


def normalize_mode(mode: str) -> str:
    """Validate and normalize mode value."""
    normalized = mode.strip().lower()
    if normalized not in VALID_MODES:
        allowed = ", ".join(VALID_MODES)
        raise ValueError(f"Unsupported mode '{mode}'. Allowed values: {allowed}")
    return normalized


def set_mode(project_dir: Path, mode: str) -> dict[str, Any]:
    """Apply one of dopetask/chatx/both/none across all managed instruction files."""
    normalized_mode = normalize_mode(mode)
    before_hashes = _read_instruction_hashes(project_dir)

    pack_changes: dict[str, int] = {}
    for pack_name, enabled in MODE_TO_PACK_ENABLED[normalized_mode].items():
        # Reuse existing toggle commands rather than reimplementing pack parsing.
        result = enable_pack(project_dir, pack_name) if enabled else disable_pack(project_dir, pack_name)
        pack_changes[pack_name] = sum(
            1 for item in result["changes"] if item["status"] in {"created", "updated"}
        )

    status = _normalize_status(project_status(project_dir))
    after_hashes = _read_instruction_hashes(project_dir)
    changed_files = sorted(
        filename
        for filename in after_hashes
        if before_hashes.get(filename) != after_hashes.get(filename)
    )

    generated_dir = project_dir / "generated"
    generated_dir.mkdir(parents=True, exist_ok=True)
    report_path = generated_dir / "PROJECT_MODE_REPORT.md"
    report_path.write_text(
        _render_mode_report(
            project_dir=project_dir,
            mode=normalized_mode,
            pack_changes=pack_changes,
            status=status,
            changed_files=changed_files,
        ),
        encoding="utf-8",
    )

    return {
        "mode": normalized_mode,
        "pack_changes": pack_changes,
        "per_file_status": status,
        "changed_files": changed_files,
        "report_path": str(report_path),
    }


def _read_instruction_hashes(project_dir: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for filename in MANAGED_FILES:
        path = project_dir / filename
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8")
        hashes[filename] = sha256(content.encode("utf-8")).hexdigest()
    return hashes


def _normalize_status(status_result: dict[str, Any]) -> dict[str, dict[str, str]]:
    normalized: dict[str, dict[str, str]] = {}
    for item in status_result["files"]:
        filename = Path(item["file"]).name
        if not item["exists"]:
            normalized[filename] = {"dopetask": "missing", "chatx": "missing"}
            continue
        normalized[filename] = {
            "dopetask": "enabled" if item["packs"]["dopetask"] else "disabled",
            "chatx": "enabled" if item["packs"]["chatx"] else "disabled",
        }
    return normalized


def _render_mode_report(
    project_dir: Path,
    mode: str,
    pack_changes: dict[str, int],
    status: dict[str, dict[str, str]],
    changed_files: list[str],
) -> str:
    lines: list[str] = [
        "# PROJECT_MODE_REPORT",
        "",
        f"- project_dir: {project_dir}",
        f"- selected_mode: {mode}",
        f"- dopetask_changed_files: {pack_changes.get('dopetask', 0)}",
        f"- chatx_changed_files: {pack_changes.get('chatx', 0)}",
        "",
        "## Per-file Pack Status",
        "",
    ]

    for filename in sorted(status):
        lines.append(
            f"- {filename}: dopetask={status[filename]['dopetask']} chatx={status[filename]['chatx']}"
        )

    lines.extend(["", "## Files Changed", ""])
    if changed_files:
        for filename in changed_files:
            lines.append(f"- {filename}")
    else:
        lines.append("- (none)")

    lines.append("")
    return "\n".join(lines)
