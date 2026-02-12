"""Task runner types."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ProjectIdentity:
    """Task packet project identity declaration."""

    project_id: str
    intended_repo: str | None = None


@dataclass
class TaskPacketInfo:
    """Parsed task packet information."""

    id: str
    title: str
    path: str
    sha256: str
    allowlist: list[str]
    sources: list[str]
    verification_commands: list[str]
    sections: dict[str, str]
    project_identity: ProjectIdentity | None = None


@dataclass
class RunWorkspace:
    """Run workspace information."""

    root: str
    files: list[dict[str, str]]
