"""Compliance gate types."""

from dataclasses import dataclass
from typing import List


@dataclass
class Violation:
    """Single compliance violation."""
    
    type: str  # allowlist_violation, missing_verification_evidence, etc.
    message: str
    files: List[str]


@dataclass
class AllowlistDiff:
    """Result of allowlist compliance check."""
    
    run_id: str
    task_id: str
    task_title: str
    allowlist: List[str]
    diff_mode_used: str
    allowed_files: List[str]
    disallowed_files: List[str]
    violations: List[Violation]
    diff_hash: str
