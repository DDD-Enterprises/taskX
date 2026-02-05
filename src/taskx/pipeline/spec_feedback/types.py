"""Types for spec feedback."""

from dataclasses import dataclass
from typing import Any


@dataclass
class Evidence:
    """Evidence linking a patch to a claim."""

    run_id: str
    claim_id: str


@dataclass
class Patch:
    """A patch operation for the task queue."""

    task_id: str
    op: str  # set_priority, set_risk, append_note, set_status
    value: Any  # string or int depending on op
    reason: str
    evidence: list[Evidence]
