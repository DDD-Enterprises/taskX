"""TaskX Ops Module — operator system prompt management.

Public API for programmatic access to operator prompt compilation,
block injection, diagnostics, and instruction-file discovery.
"""

from dopetask.ops.blocks import find_block, inject_block, update_file
from dopetask.ops.conflicts import check_conflicts
from dopetask.ops.discover import discover_instruction_file, get_sidecar_path
from dopetask.ops.doctor import extract_operator_blocks, get_canonical_target, run_doctor
from dopetask.ops.export import calculate_hash, export_prompt, load_profile, write_if_changed

__all__ = [
    # blocks
    "find_block",
    "inject_block",
    "update_file",
    # conflicts
    "check_conflicts",
    # discover
    "discover_instruction_file",
    "get_sidecar_path",
    # doctor
    "extract_operator_blocks",
    "get_canonical_target",
    "run_doctor",
    # export
    "calculate_hash",
    "export_prompt",
    "load_profile",
    "write_if_changed",
]
