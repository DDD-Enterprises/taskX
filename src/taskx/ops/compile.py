"""Compatibility surface for ops prompt compilation.

Historically, the ops toolchain exposed hashing/compilation helpers via
``taskx.ops.compile``. The implementation has since moved to
``taskx.ops.export`` but the import surface remains for stability.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from taskx.ops.export import (
    calculate_hash as _calculate_hash,
)
from taskx.ops.export import (
    export_prompt,
)
from taskx.ops.export import (
    load_profile as _load_profile,
)

if TYPE_CHECKING:
    from pathlib import Path


def calculate_hash(content: str) -> str:
    """Compatibility wrapper for legacy import path."""

    return _calculate_hash(content)


def load_profile(path: Path) -> dict[str, Any]:
    """Compatibility wrapper for legacy import path."""

    return _load_profile(path)


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
