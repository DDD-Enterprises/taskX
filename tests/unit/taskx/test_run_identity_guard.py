"""Tests for run-directory identity binding."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from dopetask.guard.identity import (
    RepoIdentity,
    RunIdentity,
    assert_repo_run_identity,
    ensure_run_identity,
)
from dopetask.obs.run_artifacts import RUN_IDENTITY_FILENAME

if TYPE_CHECKING:
    from pathlib import Path


def test_run_identity_mismatch_refuses_with_exact_message() -> None:
    """Run directory from another project should hard-fail."""
    repo_identity = RepoIdentity(
        project_id="dopetask",
        project_slug="dopeTask",
        repo_remote_hint="dopeTask",
        packet_required_header=True,
    )
    run_identity = RunIdentity(
        schema_version="1.0",
        project_id="adops",
        repo_root="/tmp/other",
        origin_url="git@github.com:example/adops.git",
        head_sha="abc123",
        timestamp_utc="2026-02-12T00:00:00Z",
    )

    with pytest.raises(RuntimeError) as exc_info:
        assert_repo_run_identity(repo_identity, run_identity)

    assert str(exc_info.value) == (
        "ERROR: Run directory project_id 'adops' does not match repo project_id 'dopetask'.\n"
        "Refusing to run."
    )


def test_ensure_run_identity_writes_file_when_missing(tmp_path: Path) -> None:
    """Missing RUN_IDENTITY.json should be written with current repo identity."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    run_dir = tmp_path / "out" / "runs" / "RUN_X"

    repo_identity = RepoIdentity(
        project_id="dopetask",
        project_slug="dopeTask",
        repo_remote_hint="dopeTask",
        packet_required_header=True,
    )

    written = ensure_run_identity(run_dir, repo_identity, repo_root)

    identity_path = run_dir / RUN_IDENTITY_FILENAME
    assert identity_path.exists()

    payload = json.loads(identity_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "1.0"
    assert payload["project_id"] == "dopetask"
    assert payload["repo_root"] == str(repo_root.resolve())
    assert payload["timestamp_utc"]

    assert written.project_id == "dopetask"
    assert written.repo_root == str(repo_root.resolve())
