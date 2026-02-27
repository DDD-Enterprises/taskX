"""Deterministic dopeTask/ChatX directive pack toggles."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from dopetask.project.common import (
    DISABLED_TEXT,
    MANAGED_FILES,
    MANAGED_TEMPLATE_FILES,
    PACK_ORDER,
    apply_block_content,
    extract_block_content,
    file_hash,
    is_enabled_content,
    read_pack_text,
    read_template_text,
)

VALID_PACKS = {"dopetask", "chatx"}


def apply_pack(file_path: Path, pack_name: str, enabled: bool) -> dict[str, Any]:
    """Apply a single pack toggle to one file path."""
    normalized_pack = _normalize_pack(pack_name)
    existed = file_path.exists()

    if existed:
        original_text = file_path.read_text(encoding="utf-8")
    else:
        template_name = MANAGED_TEMPLATE_FILES.get(file_path.name)
        if template_name is None:
            raise ValueError(f"Unsupported managed file: {file_path.name}")
        original_text = read_template_text(template_name)

    before_hash = file_hash(original_text) if existed else None
    payload = read_pack_text(normalized_pack) if enabled else DISABLED_TEXT
    updated_text, update = apply_block_content(original_text, normalized_pack, payload)

    changed = (not existed) or (updated_text != original_text)
    if changed:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(updated_text, encoding="utf-8")

    return {
        "file": str(file_path),
        "status": "created" if not existed else ("updated" if changed else "unchanged"),
        "pack": normalized_pack,
        "enabled": enabled,
        "before_hash": before_hash,
        "after_hash": file_hash(updated_text),
        "block_added": update.block_added,
        "content_changed": update.content_changed,
    }


def enable_pack(project_dir: Path, pack_name: str) -> dict[str, Any]:
    """Enable a pack across all managed project files."""
    return _toggle_pack(project_dir=project_dir, pack_name=pack_name, enabled=True)


def disable_pack(project_dir: Path, pack_name: str) -> dict[str, Any]:
    """Disable a pack across all managed project files."""
    return _toggle_pack(project_dir=project_dir, pack_name=pack_name, enabled=False)


def project_status(project_dir: Path) -> dict[str, Any]:
    """Report per-file directive pack status."""
    files: list[dict[str, Any]] = []
    for filename in MANAGED_FILES:
        file_path = project_dir / filename
        if not file_path.exists():
            files.append(
                {
                    "file": str(file_path),
                    "exists": False,
                    "packs": dict.fromkeys(PACK_ORDER, False),
                }
            )
            continue

        text = file_path.read_text(encoding="utf-8")
        packs = {
            pack: is_enabled_content(extract_block_content(text, pack))
            for pack in PACK_ORDER
        }
        files.append(
            {
                "file": str(file_path),
                "exists": True,
                "packs": packs,
            }
        )

    return {"project_dir": str(project_dir), "files": files}


def _toggle_pack(project_dir: Path, pack_name: str, enabled: bool) -> dict[str, Any]:
    normalized_pack = _normalize_pack(pack_name)
    project_dir.mkdir(parents=True, exist_ok=True)

    changes: list[dict[str, Any]] = []
    for filename in MANAGED_FILES:
        changes.append(apply_pack(project_dir / filename, normalized_pack, enabled))

    report_path = project_dir / "PROJECT_PATCH_REPORT.md"
    report_path.write_text(
        _render_patch_report(
            project_dir=project_dir,
            pack_name=normalized_pack,
            enabled=enabled,
            changes=changes,
        ),
        encoding="utf-8",
    )

    return {
        "project_dir": str(project_dir),
        "pack": normalized_pack,
        "enabled": enabled,
        "changes": changes,
        "report_path": str(report_path),
    }


def _normalize_pack(pack_name: str) -> str:
    normalized = pack_name.strip().lower()
    if normalized not in VALID_PACKS:
        raise ValueError(f"Unsupported directive pack: {pack_name}")
    return normalized


def _render_patch_report(
    project_dir: Path,
    pack_name: str,
    enabled: bool,
    changes: list[dict[str, Any]],
) -> str:
    lines: list[str] = [
        "# PROJECT_PATCH_REPORT",
        "",
        f"- project_dir: {project_dir}",
        f"- operation: {'enable' if enabled else 'disable'}",
        f"- pack: {pack_name}",
        "",
        "## Files Changed",
        "",
    ]

    for change in changes:
        lines.append(f"### {Path(change['file']).name}")
        lines.append(f"- status: {change['status']}")
        lines.append(f"- block_added: {change['block_added']}")
        lines.append(f"- content_changed: {change['content_changed']}")
        if change["before_hash"] is not None:
            lines.append(f"- before_hash: {change['before_hash']}")
        lines.append(f"- after_hash: {change['after_hash']}")
        lines.append("")

    return "\n".join(lines)

