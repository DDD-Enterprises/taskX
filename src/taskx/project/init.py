"""Project initialization for supervisor and LLM config files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from taskx.project.common import (
    BUNDLE_FILE,
    BUNDLE_TEMPLATE_FILE,
    DISABLED_TEXT,
    MANAGED_FILES,
    MANAGED_TEMPLATE_FILES,
    apply_pack_map,
    file_hash,
    read_pack_text,
    read_template_text,
)

VALID_PRESETS = {"taskx", "chatx", "both", "none"}


def init_project(out_dir: Path, preset: str) -> dict[str, Any]:
    """Create/update project files and emit PROJECT_INIT_REPORT.md."""
    normalized_preset = preset.strip().lower()
    if normalized_preset not in VALID_PRESETS:
        raise ValueError(f"Unsupported preset: {preset}")

    out_dir.mkdir(parents=True, exist_ok=True)
    selected_packs = _selected_packs(normalized_preset)
    pack_content = {
        "taskx": read_pack_text("taskx") if "taskx" in selected_packs else DISABLED_TEXT,
        "chatx": read_pack_text("chatx") if "chatx" in selected_packs else DISABLED_TEXT,
    }

    files_summary: list[dict[str, Any]] = []
    for filename in MANAGED_FILES:
        file_path = out_dir / filename
        existed = file_path.exists()
        original_text = (
            file_path.read_text(encoding="utf-8")
            if existed
            else read_template_text(MANAGED_TEMPLATE_FILES[filename])
        )
        before_hash = file_hash(original_text) if existed else None

        updated_text, updates = apply_pack_map(original_text, pack_content)
        changed = (not existed) or (updated_text != original_text)
        if changed:
            file_path.write_text(updated_text, encoding="utf-8")

        files_summary.append(
            {
                "file": str(file_path),
                "status": "created" if not existed else ("updated" if changed else "unchanged"),
                "before_hash": before_hash,
                "after_hash": file_hash(updated_text),
                "blocks": {
                    pack_name: {
                        "added": update.block_added,
                        "content_changed": update.content_changed,
                    }
                    for pack_name, update in updates.items()
                },
            }
        )

    bundle_summary = _ensure_bundle_file(out_dir)
    report_path = out_dir / "PROJECT_INIT_REPORT.md"
    report_path.write_text(
        _render_report(out_dir=out_dir, preset=normalized_preset, files_summary=files_summary, bundle=bundle_summary),
        encoding="utf-8",
    )

    return {
        "out_dir": str(out_dir),
        "preset": normalized_preset,
        "files": files_summary,
        "bundle": bundle_summary,
        "report_path": str(report_path),
    }


def _selected_packs(preset: str) -> set[str]:
    if preset == "taskx":
        return {"taskx"}
    if preset == "chatx":
        return {"chatx"}
    if preset == "both":
        return {"taskx", "chatx"}
    return set()


def _ensure_bundle_file(out_dir: Path) -> dict[str, Any]:
    bundle_path = out_dir / BUNDLE_FILE
    default_text = read_template_text(BUNDLE_TEMPLATE_FILE)

    if not bundle_path.exists():
        bundle_path.write_text(default_text, encoding="utf-8")
        return {
            "file": str(bundle_path),
            "status": "created",
            "before_hash": None,
            "after_hash": file_hash(default_text),
        }

    existing = bundle_path.read_text(encoding="utf-8")
    return {
        "file": str(bundle_path),
        "status": "unchanged",
        "before_hash": file_hash(existing),
        "after_hash": file_hash(existing),
    }


def _render_report(
    out_dir: Path,
    preset: str,
    files_summary: list[dict[str, Any]],
    bundle: dict[str, Any],
) -> str:
    lines: list[str] = [
        "# PROJECT_INIT_REPORT",
        "",
        f"- output_dir: {out_dir}",
        f"- preset: {preset}",
        "",
        "## Files",
        "",
    ]

    for item in files_summary:
        lines.append(f"### {Path(item['file']).name}")
        lines.append(f"- status: {item['status']}")
        if item["before_hash"] is not None:
            lines.append(f"- before_hash: {item['before_hash']}")
        lines.append(f"- after_hash: {item['after_hash']}")
        for pack_name, block in item["blocks"].items():
            lines.append(
                f"- {pack_name}_block: added={block['added']} content_changed={block['content_changed']}"
            )
        lines.append("")

    lines.extend(
        [
            "## Bundle",
            "",
            f"- file: {Path(bundle['file']).name}",
            f"- status: {bundle['status']}",
        ]
    )
    if bundle["before_hash"] is not None:
        lines.append(f"- before_hash: {bundle['before_hash']}")
    lines.append(f"- after_hash: {bundle['after_hash']}")
    lines.append("")

    return "\n".join(lines)

