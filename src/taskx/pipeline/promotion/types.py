"""Promotion gate types."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Evidence:
    """Evidence file used in promotion decision."""
    
    kind: str  # allowlist_diff, run_envelope, run_summary, evidence_md
    path: str


@dataclass
class PromotionToken:
    """Result of promotion gate check."""
    
    run_id: str
    status: str  # passed or failed
    reasons: List[str]
    evidence: List[Evidence]
    token_hash: str
    
    # Input paths
    run_dir: str
    allowlist_diff_path: str
    run_envelope_path: str
    run_summary_path: Optional[str]
