"""Task runner types."""

from __future__ import annotations

import typing
from dataclasses import dataclass


@dataclass
class ProjectIdentity:
    """Task packet project identity declaration."""

    project_id: str
    intended_repo: typing.Optional[str] = None


@dataclass
class CommitStep:
    """Single commit step from optional COMMIT PLAN section."""

    step_id: str
    message: str
    allowlist: list[str]
    verify: typing.Optional[list[str]]


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
    commit_plan: typing.Optional[list[CommitStep]]
    sections: dict[str, str]
    project_identity: typing.Optional[ProjectIdentity] = None


@dataclass
class RunWorkspace:
    """Run workspace information."""

    root: str
    files: list[dict[str, str]]
