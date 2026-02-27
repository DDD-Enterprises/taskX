"""Runner adapter protocol for orchestrator execution."""

from __future__ import annotations

from typing import Protocol


class RunnerAdapter(Protocol):
    """Protocol implemented by dopeTask runner adapters."""

    runner_id: str

    def prepare(self, packet: dict, route_plan: dict) -> dict:
        """Build a deterministic runspec."""

    def run(self, runspec: dict) -> dict:
        """Execute a runspec and return raw result payload."""

    def normalize(self, result: dict) -> dict:
        """Normalize a raw runner result into a stable report fragment."""
