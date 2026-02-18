"""Compatibility surface for ops prompt compilation.

Historically, the ops toolchain exposed hashing/compilation helpers via
``taskx.ops.compile``. The implementation has since moved to
``taskx.ops.export`` but the import surface remains for stability.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from taskx.ops.export import calculate_hash, export_prompt, load_profile


def compile_prompt(
    profile: dict[str, Any],
    templates_dir: Path,
    platform_override: str | None = None,
    model_override: str | None = None,
    *,
    taskx_version: str = "UNKNOWN",
    git_hash: str = "UNKNOWN",
) -> str:
    """Compile a unified operator system prompt from profile + templates."""

    return export_prompt(
        profile,
        templates_dir,
        platform_override=platform_override,
        model_override=model_override,
        taskx_version=taskx_version,
        git_hash=git_hash,
    )

