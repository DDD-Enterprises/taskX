"""Proof pack writer for dopetask tp run."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from dopetask.artifacts.canonical_json import write_json
from dopetask.ops.tp_git.exec import run_git


@dataclass(frozen=True)
class ProofPaths:
    """Resolved proof-pack output directories."""

    repo_root: Path
    tp_id: str
    run_id: str
    run_dir: Path


def build_run_id(*, tp_id: str, repo_root: Path) -> str:
    """Build deterministic run id with UTC timestamp and current short sha."""
    stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    short_sha = run_git(["rev-parse", "--short", "HEAD"], repo_root=repo_root).stdout.strip() or "unknown"
    return f"{tp_id}_{stamp}_{short_sha}"


def resolve_paths(*, repo_root: Path, tp_id: str, run_id: str) -> ProofPaths:
    """Resolve canonical run directory for TP receipts."""
    run_dir = (repo_root / "runs" / "tp" / tp_id / run_id).resolve()
    return ProofPaths(repo_root=repo_root, tp_id=tp_id, run_id=run_id, run_dir=run_dir)


class ProofWriter:
    """Writer abstraction for deterministic TP run artifacts."""

    def __init__(self, paths: ProofPaths):
        self.paths = paths
        self.paths.run_dir.mkdir(parents=True, exist_ok=True)

    def write_text(self, name: str, content: str) -> Path:
        """Write a text artifact."""
        target = self.paths.run_dir / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return target

    def append_log(self, name: str, content: str) -> Path:
        """Append textual content to an artifact file."""
        target = self.paths.run_dir / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as handle:
            handle.write(content)
        return target

    def write_json(self, name: str, obj: dict[str, Any]) -> Path:
        """Write canonical JSON artifact."""
        target = self.paths.run_dir / name
        write_json(target, obj)
        return target
