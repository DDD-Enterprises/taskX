"""Deterministic manual handoff chunk builder."""

from __future__ import annotations

import re
from typing import Any


def build_handoff_chunks(packet: dict[str, Any], route_plan: dict[str, Any]) -> list[dict[str, Any]]:
    """Build deterministic per-step manual handoff chunks."""
    del packet
    packet_path = str(route_plan.get("packet_path", ""))
    run_dir = str(route_plan.get("run_dir", ""))
    resume_command = f"dopetask orchestrate {packet_path}".strip()

    chunks: list[dict[str, Any]] = []
    for step in route_plan.get("steps", []):
        if not isinstance(step, dict):
            continue

        step_name = str(step.get("step", "")).strip()
        if not step_name:
            continue

        runner_id = _map_runner_id(str(step.get("runner") or "unknown"))
        model_id = str(step.get("model") or "unspecified")
        sentinel_name = f"STEP_{_normalize_step_token(step_name)}.DONE"
        sentinel_path = f"{run_dir}/{sentinel_name}" if run_dir else sentinel_name

        instructions_block = "\n".join(
            [
                f"Runner: {runner_id}",
                f"Model: {model_id}",
                f"Input: {packet_path}",
                f"Output dir: {run_dir}",
                f"After completion: create {sentinel_path}",
            ]
        )

        chunks.append(
            {
                "step": step_name,
                "runner_id": runner_id,
                "model_id": model_id,
                "instructions_block": instructions_block,
                "expected_artifacts": [sentinel_name],
                "resume_command": resume_command,
            }
        )
    return chunks


def render_handoff_chunks(handoff_chunks: list[dict[str, Any]]) -> str:
    """Render deterministic stdout text for manual handoff chunks."""
    total = len(handoff_chunks)
    if total == 0:
        return ""

    blocks: list[str] = []
    for index, chunk in enumerate(handoff_chunks, start=1):
        blocks.append(f"HANDOFF CHUNK {index}/{total} ({chunk['step']})")
        blocks.append(str(chunk["instructions_block"]))
        if index < total:
            blocks.append("")

    return "\n".join(blocks)


def _normalize_step_token(step: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9]+", "_", step.strip().upper())
    return normalized.strip("_") or "STEP"


def _map_runner_id(runner_id: str) -> str:
    mapping = {
        "codex_desktop": "codex-cli",
        "claude_code": "claude-code",
        "copilot_cli": "copilot-cli",
    }
    return mapping.get(runner_id, runner_id)
