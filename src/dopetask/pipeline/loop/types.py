"""Types for loop orchestrator."""

import typing
from dataclasses import dataclass
from pathlib import Path


@dataclass
class LoopInputs:
    """Inputs for loop orchestration."""

    root: Path
    mode: str  # mvp, hardening, full
    max_packets: int
    seed: int
    run_task: typing.Optional[str]
    run_id: typing.Optional[str]
    collect_evidence: bool
    feedback: bool


@dataclass
class StageResult:
    """Result from a single stage execution."""

    enabled: bool
    status: str  # skipped, ok, failed
    started_at: typing.Optional[str]
    ended_at: typing.Optional[str]
    out_dir: typing.Optional[str]
    inputs: dict
    outputs: list[str]
    hashes: dict
    error: typing.Optional[str]
