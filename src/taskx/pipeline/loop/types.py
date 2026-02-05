"""Types for loop orchestrator."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class LoopInputs:
    """Inputs for loop orchestration."""

    root: Path
    mode: str  # mvp, hardening, full
    max_packets: int
    seed: int
    run_task: str | None
    run_id: str | None
    collect_evidence: bool
    feedback: bool


@dataclass
class StageResult:
    """Result from a single stage execution."""

    enabled: bool
    status: str  # skipped, ok, failed
    started_at: str | None
    ended_at: str | None
    out_dir: str | None
    inputs: dict
    outputs: list[str]
    hashes: dict
    error: str | None
