"""Repo/task packet/run identity guard helpers."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from taskx.obs.run_artifacts import (
    PROJECT_IDENTITY_PATH,
    RUN_IDENTITY_FILENAME,
)

if TYPE_CHECKING:
    from taskx.pipeline.task_runner.types import ProjectIdentity


MISSING_PROJECT_HEADER_REFUSAL = (
    "ERROR: Task Packet missing required PROJECT IDENTITY header.\n"
    "Refusing to run."
)


@dataclass(frozen=True)
class RepoIdentity:
    """Canonical identity of the active repository."""

    project_id: str
    project_slug: str | None
    repo_remote_hint: str | None
    packet_required_header: bool


GUARD_ARTIFACT_PATH = Path("out/taskx_guard")
TASKX_PROJECT_ID = "taskx.core"
SAFE_INVOCATION = "PYTHONPATH=src python -m taskx ..."


@dataclass(frozen=True)
class RunIdentity:
    """Identity binding persisted in each run directory."""

    schema_version: str
    project_id: str
    repo_root: str
    origin_url: str | None
    head_sha: str | None
    timestamp_utc: str



def load_repo_identity(repo_root: Path) -> RepoIdentity:
    """Load canonical repo identity from `.taskx/project.json`."""
    identity_path = (repo_root / PROJECT_IDENTITY_PATH).resolve()
    try:
        payload = json.loads(identity_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RuntimeError(f"Repo identity file not found: {identity_path}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid repo identity JSON: {identity_path}: {exc}") from exc

    if not isinstance(payload, dict):
        raise RuntimeError(f"Invalid repo identity payload in {identity_path}")

    project_id_value = payload.get("project_id")
    if not isinstance(project_id_value, str):
        raise RuntimeError(f"'project_id' must be a string in {identity_path}")
    project_id = project_id_value.strip()
    if not project_id:
        raise RuntimeError(f"Missing required key 'project_id' in {identity_path}")

    project_slug = _to_optional_str(payload.get("project_slug"))
    repo_remote_hint = _to_optional_str(payload.get("repo_remote_hint"))
    packet_required_header = _to_bool(payload.get("packet_required_header"), default=False)

    return RepoIdentity(
        project_id=project_id,
        project_slug=project_slug,
        repo_remote_hint=repo_remote_hint,
        packet_required_header=packet_required_header,
    )



def extract_origin_url(repo_root: Path) -> str | None:
    """Best-effort git origin URL lookup."""
    return _git_output(repo_root, "remote", "get-url", "origin")



def load_run_identity(run_dir: Path) -> RunIdentity | None:
    """Load RUN_IDENTITY.json from run directory when present."""
    identity_path = run_dir / RUN_IDENTITY_FILENAME
    if not identity_path.exists():
        return None

    try:
        payload = json.loads(identity_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid run identity JSON: {identity_path}: {exc}") from exc

    return _run_identity_from_payload(payload, identity_path)



def ensure_run_identity(
    run_dir: Path,
    repo_identity: RepoIdentity,
    repo_root: Path,
) -> RunIdentity:
    """Ensure RUN_IDENTITY.json exists and is bound to the current repo identity."""
    run_dir.mkdir(parents=True, exist_ok=True)

    existing = load_run_identity(run_dir)
    if existing is not None:
        assert_repo_run_identity(repo_identity, existing)
        return existing

    run_identity = RunIdentity(
        schema_version="1.0",
        project_id=repo_identity.project_id,
        repo_root=str(repo_root.resolve()),
        origin_url=extract_origin_url(repo_root),
        head_sha=_git_output(repo_root, "rev-parse", "HEAD"),
        timestamp_utc=_timestamp_utc(),
    )
    identity_path = run_dir / RUN_IDENTITY_FILENAME
    identity_path.write_text(
        json.dumps(
            {
                "schema_version": run_identity.schema_version,
                "project_id": run_identity.project_id,
                "repo_root": run_identity.repo_root,
                "origin_url": run_identity.origin_url,
                "head_sha": run_identity.head_sha,
                "timestamp_utc": run_identity.timestamp_utc,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return run_identity



def assert_repo_packet_identity(
    repo_identity: RepoIdentity,
    packet_identity: ProjectIdentity | None,
) -> None:
    """Hard-fail when task packet identity mismatches repo identity."""
    if packet_identity is None:
        if repo_identity.packet_required_header:
            raise RuntimeError(MISSING_PROJECT_HEADER_REFUSAL)
        return

    packet_project_id = packet_identity.project_id.strip()
    if packet_project_id != repo_identity.project_id:
        raise RuntimeError(
            f"ERROR: Task Packet project_id '{packet_project_id}' does not match repo project_id '{repo_identity.project_id}'.\n"
            "Refusing to run. Use the correct repo or correct packet."
        )



def assert_repo_run_identity(repo_identity: RepoIdentity, run_identity: RunIdentity) -> None:
    """Hard-fail when run identity mismatches repo identity."""
    if run_identity.project_id != repo_identity.project_id:
        raise RuntimeError(
            f"ERROR: Run directory project_id '{run_identity.project_id}' does not match repo project_id '{repo_identity.project_id}'.\n"
            "Refusing to run."
        )



def assert_repo_branch_identity(repo_identity: RepoIdentity, branch_name: str) -> None:
    """Hard-fail when `tp/<project_id>/...` branch identity mismatches current repo."""
    if not branch_name.startswith("tp/"):
        return

    parts = branch_name.split("/", 2)
    if len(parts) < 2:
        return

    branch_project_id = parts[1].strip()
    if branch_project_id != repo_identity.project_id:
        raise RuntimeError(
            f"ERROR: Current branch project_id '{branch_project_id}' does not match repo project_id '{repo_identity.project_id}'.\n"
            "Refusing to run."
        )



def run_identity_origin_warning(
    repo_identity: RepoIdentity,
    run_identity: RunIdentity,
) -> str | None:
    """Return soft warning when run origin URL does not match repo hint."""
    return origin_hint_warning(repo_identity.repo_remote_hint, run_identity.origin_url)



def origin_hint_warning(repo_remote_hint: str | None, origin_url: str | None) -> str | None:
    """Build a one-line warning for remote hint mismatches."""
    if origin_url is None:
        return "[taskx][WARNING] origin URL not available"
    if repo_remote_hint and repo_remote_hint not in origin_url:
        return (
            "[taskx][WARNING] origin URL does not match "
            f"repo_remote_hint='{repo_remote_hint}' (origin='{origin_url}')"
        )
    return None



def _run_identity_from_payload(payload: Any, identity_path: Path) -> RunIdentity:
    if not isinstance(payload, dict):
        raise RuntimeError(f"Invalid run identity payload in {identity_path}")

    project_id = str(payload.get("project_id", "")).strip()
    if not project_id:
        raise RuntimeError(f"Missing required key 'project_id' in {identity_path}")

    schema_version = str(payload.get("schema_version", "1.0")).strip() or "1.0"
    repo_root = str(payload.get("repo_root", "")).strip()
    timestamp_utc = str(payload.get("timestamp_utc", "")).strip()

    return RunIdentity(
        schema_version=schema_version,
        project_id=project_id,
        repo_root=repo_root,
        origin_url=_to_optional_str(payload.get("origin_url")),
        head_sha=_to_optional_str(payload.get("head_sha")),
        timestamp_utc=timestamp_utc,
    )



def _timestamp_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")



def _git_output(repo_root: Path, *args: str) -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "-C", str(repo_root), *args],
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return None

    text = out.decode("utf-8", errors="replace").strip()
    return text or None



def _to_optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None



def _to_bool(value: object, *, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "on"}:
            return True
        if normalized in {"false", "0", "no", "off"}:
            return False
    if value is None:
        return default
    return bool(value)


class RepoIdentityGuardError(RuntimeError):
    def __init__(self, expected_project_id: str, observed_project_id: str | None, repo_root: Path):
        observed = observed_project_id or "MISSING"
        message = (
            "REFUSAL: repo identity mismatch\n"
            f"expected_project_id: {expected_project_id}\n"
            f"observed_project_id: {observed}\n"
            f"repo_root: {repo_root}\n"
            f"hint: You are likely running the wrong repo or a shadowed taskx install. "
            f"Use {SAFE_INVOCATION}"
        )
        super().__init__(message)
        self.expected_project_id = expected_project_id
        self.observed_project_id = observed
        self.repo_root = repo_root


def read_observed_project_id(repo_root: Path) -> str | None:
    try:
        identity = load_repo_identity(repo_root)
        return identity.project_id
    except RuntimeError:
        return None


def assert_repo_identity(
    repo_root: Path,
    *,
    expected_project_id: str | None = None,
    report_dir: Path | None = None,
) -> RepoIdentity:
    taskxroot = repo_root / ".taskxroot"
    project_file = repo_root / PROJECT_IDENTITY_PATH

    if not taskxroot.exists():
        raise RepoIdentityGuardError(expected_project_id or TASKX_PROJECT_ID, None, repo_root)
    if not project_file.exists():
        raise RepoIdentityGuardError(expected_project_id or TASKX_PROJECT_ID, None, repo_root)

    identity = load_repo_identity(repo_root)
    if expected_project_id and identity.project_id != expected_project_id:
        raise RepoIdentityGuardError(expected_project_id, identity.project_id, repo_root)
    effective_expected = expected_project_id or identity.project_id

    artifacts_dir = report_dir or (repo_root / GUARD_ARTIFACT_PATH)
    _write_guard_artifacts(
        artifacts_dir,
        expected_project_id=effective_expected,
        observed_project_id=identity.project_id,
        files={
            ".taskxroot": True,
            ".taskx/project.json": project_file.exists(),
        },
    )

    return identity


def _write_guard_artifacts(
    directory: Path,
    *,
    expected_project_id: str,
    observed_project_id: str,
    files: dict[str, bool],
) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    payload = {
        "check": "repo_identity",
        "ok": True,
        "expected_project_id": expected_project_id,
        "observed_project_id": observed_project_id,
        "files": files,
    }
    json_path = directory / "REPO_IDENTITY.json"
    md_path = directory / "REPO_IDENTITY.md"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_lines = [
        "# Repo Identity Check",
        "",
        "- ok: true",
        f"- expected_project_id: {expected_project_id}",
        f"- observed_project_id: {observed_project_id}",
    ]
    for key, present in files.items():
        md_lines.append(f"- {key}: {present}")
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
