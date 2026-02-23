"""Task packet manifest helpers for run auditability and replay checks."""

from __future__ import annotations

import json
import re
import shlex
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterable

Manifest = dict[str, Any]

MANIFEST_FILENAME = "TASK_PACKET_MANIFEST.json"
COMMAND_LOG_DIR = "_manifest_logs"
DETERMINISTIC_TIMESTAMP = "1970-01-01T00:00:00Z"
MAX_LOG_CHARS = 100_000
REDACTED_VALUE = "[REDACTED]"

_SENSITIVE_KEYS = {
    "access_token",
    "api_key",
    "apikey",
    "auth_token",
    "bearer",
    "client_secret",
    "password",
    "passphrase",
    "private_key",
    "secret",
    "session_token",
    "token",
}
_SENSITIVE_SUFFIXES = (
    "_token",
    "_secret",
    "_password",
    "_passphrase",
    "_api_key",
    "_apikey",
    "_private_key",
)
_SENSITIVE_FLAG_PATTERN = re.compile(
    r"(?i)(--(?:access-token|api-key|apikey|auth-token|client-secret|"
    r"password|passphrase|private-key|secret|session-token|token))(=|\s+)(\S+)"
)
_SENSITIVE_ENV_PATTERN = re.compile(
    r"(?i)\b([A-Z0-9_]*(?:TOKEN|SECRET|PASSWORD|PASSPHRASE|API_KEY|APIKEY|PRIVATE_KEY)[A-Z0-9_]*)=(\S+)"
)


def get_timestamp(timestamp_mode: str) -> str:
    """Return timestamp for deterministic or wallclock mode."""
    if timestamp_mode == "deterministic":
        return DETERMINISTIC_TIMESTAMP
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def manifest_path(run_dir: Path) -> Path:
    """Return canonical manifest path for a run directory."""
    return Path(run_dir).resolve() / MANIFEST_FILENAME


def manifest_exists(run_dir: Path) -> bool:
    """Return True when run manifest exists."""
    return manifest_path(run_dir).exists()


def init_manifest(run_dir: Path, task_packet_id: str, mode: str, timestamp_mode: str) -> Manifest:
    """Initialize a TASK_PACKET_MANIFEST.json file for a run."""
    resolved_run_dir = Path(run_dir).resolve()
    resolved_run_dir.mkdir(parents=True, exist_ok=True)

    manifest: Manifest = {
        "schema_version": "1.0",
        "run_dir": str(resolved_run_dir),
        "run_id": _resolve_run_id(resolved_run_dir),
        "created_at": get_timestamp(timestamp_mode),
        "task_packet_id": task_packet_id,
        "mode": mode,
        "commands": [],
        "artifacts_expected": [],
        "artifacts_found": [],
        "status": "failed",
    }
    save_manifest(manifest, resolved_run_dir)
    return manifest


def record_command(
    manifest: Manifest,
    cmd: str | list[str],
    cwd: str | Path,
    exit_code: int,
    stdout_path: str | Path,
    stderr_path: str | Path,
    started_at: str | None = None,
    ended_at: str | None = None,
    timestamp_mode: str = "deterministic",
    truncated: bool = False,
    notes: str | None = None,
) -> Manifest:
    """Append a command execution record to a manifest object."""
    commands_raw = manifest.get("commands", [])
    if not isinstance(commands_raw, list):
        commands_raw = []

    next_idx = _next_command_idx(commands_raw)

    command_entry: dict[str, Any] = {
        "idx": next_idx,
        "cmd": _redact_command(cmd),
        "cwd": str(Path(cwd).resolve()),
        "started_at": started_at or get_timestamp(timestamp_mode),
        "ended_at": ended_at or get_timestamp(timestamp_mode),
        "exit_code": int(exit_code),
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "truncated": bool(truncated),
    }
    if notes:
        command_entry["notes"] = notes

    commands = [dict(item) for item in commands_raw if isinstance(item, dict)]
    commands.append(command_entry)
    commands.sort(key=lambda item: int(item.get("idx", 0)))
    manifest["commands"] = commands
    return manifest


def finalize_manifest(
    manifest: Manifest,
    artifacts_expected: Iterable[str],
    artifacts_found: Iterable[str],
    status: str,
    notes: str | None = None,
) -> Manifest:
    """Finalize expected/found artifacts and overall status for a manifest."""
    manifest["artifacts_expected"] = _sorted_unique_strings(artifacts_expected)
    manifest["artifacts_found"] = _sorted_unique_strings(artifacts_found)
    manifest["status"] = "passed" if status == "passed" else "failed"

    commands = manifest.get("commands", [])
    if isinstance(commands, list):
        manifest["commands"] = sorted(
            [dict(item) for item in commands if isinstance(item, dict)],
            key=lambda item: int(item.get("idx", 0)),
        )

    if notes:
        manifest["notes"] = notes
    else:
        manifest.pop("notes", None)
    return manifest


def load_manifest(run_dir: Path) -> Manifest | None:
    """Load manifest from run dir, or None when absent."""
    path = manifest_path(run_dir)
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path} is not a JSON object")
    return data


def save_manifest(manifest: Manifest, run_dir: Path) -> Path:
    """Write manifest with stable ordering and atomic replacement."""
    resolved_run_dir = Path(run_dir).resolve()
    resolved_run_dir.mkdir(parents=True, exist_ok=True)
    path = manifest_path(resolved_run_dir)

    _canonicalize_manifest(manifest)
    rendered = json.dumps(manifest, indent=2, sort_keys=True) + "\n"

    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(rendered, encoding="utf-8")
    temp_path.replace(path)
    return path


def append_command_record(
    run_dir: Path,
    cmd: str | list[str],
    cwd: Path,
    exit_code: int,
    stdout_text: str,
    stderr_text: str,
    timestamp_mode: str,
    expected_artifacts: list[str] | None = None,
    notes: str | None = None,
    started_at: str | None = None,
    ended_at: str | None = None,
) -> bool:
    """Append command execution to existing manifest and refresh artifact state."""
    manifest = load_manifest(run_dir)
    if manifest is None:
        return False

    commands = manifest.get("commands", [])
    next_idx = _next_command_idx(commands if isinstance(commands, list) else [])

    stdout_path, stderr_path, truncated = _write_command_logs(
        Path(run_dir).resolve(),
        next_idx,
        stdout_text,
        stderr_text,
    )

    record_command(
        manifest=manifest,
        cmd=cmd,
        cwd=cwd,
        exit_code=exit_code,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        started_at=started_at,
        ended_at=ended_at,
        timestamp_mode=timestamp_mode,
        truncated=truncated,
        notes=notes,
    )

    updated_expected = list(manifest.get("artifacts_expected", []))
    if expected_artifacts:
        for artifact in expected_artifacts:
            updated_expected.append(_normalize_artifact(run_dir=Path(run_dir).resolve(), artifact=artifact))

    normalized_expected = _sorted_unique_strings(updated_expected)
    found = _find_present_expected_artifacts(run_dir=Path(run_dir).resolve(), expected=normalized_expected)
    missing = [item for item in normalized_expected if item not in set(found)]
    status = "passed" if exit_code == 0 and not missing else "failed"

    finalize_manifest(
        manifest=manifest,
        artifacts_expected=normalized_expected,
        artifacts_found=found,
        status=status,
    )
    save_manifest(manifest, run_dir)
    return True


def check_manifest(run_dir: Path) -> dict[str, list[str]]:
    """Compare expected artifacts from manifest against actual filesystem state."""
    resolved_run_dir = Path(run_dir).resolve()
    manifest = load_manifest(resolved_run_dir)
    if manifest is None:
        raise FileNotFoundError(f"{manifest_path(resolved_run_dir)} not found")

    expected = _sorted_unique_strings(manifest.get("artifacts_expected", []))
    found = _find_present_expected_artifacts(run_dir=resolved_run_dir, expected=expected)
    found_set = set(found)
    missing = [item for item in expected if item not in found_set]

    present_relative = _list_run_files(resolved_run_dir)
    expected_relative = {
        item for item in expected if not Path(item).is_absolute()
    }
    extras = sorted(present_relative - expected_relative)

    return {
        "expected": expected,
        "found": found,
        "missing": missing,
        "extras": extras,
    }


def _resolve_run_id(run_dir: Path) -> str:
    envelope_path = run_dir / "RUN_ENVELOPE.json"
    if envelope_path.exists():
        try:
            payload = json.loads(envelope_path.read_text(encoding="utf-8"))
            run_id = payload.get("run_id")
            if isinstance(run_id, str) and run_id.strip():
                return run_id
        except (json.JSONDecodeError, OSError):
            pass
    return run_dir.name


def _canonicalize_manifest(manifest: Manifest) -> None:
    commands = manifest.get("commands", [])
    if isinstance(commands, list):
        manifest["commands"] = sorted(
            [dict(item) for item in commands if isinstance(item, dict)],
            key=lambda item: int(item.get("idx", 0)),
        )
    else:
        manifest["commands"] = []

    for key in ("artifacts_expected", "artifacts_found"):
        manifest[key] = _sorted_unique_strings(manifest.get(key, []))

    manifest["status"] = "passed" if manifest.get("status") == "passed" else "failed"


def _sorted_unique_strings(values: Iterable[Any]) -> list[str]:
    normalized = {str(item) for item in values if item is not None and str(item).strip()}
    return sorted(normalized)


def _next_command_idx(commands: list[Any]) -> int:
    max_idx = 0
    for item in commands:
        if not isinstance(item, dict):
            continue
        idx_value = item.get("idx")
        if isinstance(idx_value, int):
            max_idx = max(max_idx, idx_value)
    return max_idx + 1


def _truncate_output(text: str) -> tuple[str, bool]:
    if len(text) <= MAX_LOG_CHARS:
        return text, False
    truncated_text = text[:MAX_LOG_CHARS] + "\n[...TRUNCATED...]"
    return truncated_text, True


def _write_command_logs(run_dir: Path, idx: int, stdout_text: str, stderr_text: str) -> tuple[str, str, bool]:
    log_dir = run_dir / COMMAND_LOG_DIR
    log_dir.mkdir(parents=True, exist_ok=True)

    stdout_rendered, stdout_truncated = _truncate_output(stdout_text)
    stderr_rendered, stderr_truncated = _truncate_output(stderr_text)

    stdout_rel = (Path(COMMAND_LOG_DIR) / f"command_{idx:04d}.stdout.log").as_posix()
    stderr_rel = (Path(COMMAND_LOG_DIR) / f"command_{idx:04d}.stderr.log").as_posix()

    (run_dir / stdout_rel).write_text(stdout_rendered, encoding="utf-8")
    (run_dir / stderr_rel).write_text(stderr_rendered, encoding="utf-8")

    return stdout_rel, stderr_rel, stdout_truncated or stderr_truncated


def _normalize_artifact(run_dir: Path, artifact: str) -> str:
    artifact_text = str(artifact).strip()
    if not artifact_text:
        return artifact_text

    artifact_path = Path(artifact_text)
    resolved = artifact_path if artifact_path.is_absolute() else (run_dir / artifact_path).resolve()

    try:
        return resolved.relative_to(run_dir).as_posix()
    except ValueError:
        return str(resolved)


def _artifact_exists(run_dir: Path, artifact: str) -> bool:
    artifact_path = Path(artifact)
    if artifact_path.is_absolute():
        return artifact_path.exists()
    return (run_dir / artifact_path).exists()


def _find_present_expected_artifacts(run_dir: Path, expected: list[str]) -> list[str]:
    return [item for item in expected if _artifact_exists(run_dir, item)]


def _list_run_files(run_dir: Path) -> set[str]:
    files: set[str] = set()
    for path in run_dir.rglob("*"):
        if not path.is_file():
            continue

        rel = path.relative_to(run_dir).as_posix()
        if rel == MANIFEST_FILENAME:
            continue
        if rel.startswith(f"{COMMAND_LOG_DIR}/"):
            continue
        files.add(rel)
    return files


def _is_sensitive_key(key: str) -> bool:
    normalized = key.strip().lstrip("-").lower().replace("-", "_")
    if normalized in _SENSITIVE_KEYS:
        return True
    return normalized.endswith(_SENSITIVE_SUFFIXES)


def _redact_command(cmd: str | list[str]) -> str | list[str]:
    if isinstance(cmd, list):
        return _redact_tokens(cmd)

    try:
        redacted_tokens = _redact_tokens(shlex.split(cmd, posix=True))
        return shlex.join(redacted_tokens)
    except ValueError:
        partially = _SENSITIVE_FLAG_PATTERN.sub(
            lambda match: f"{match.group(1)}{match.group(2)}{REDACTED_VALUE}",
            cmd,
        )
        return _SENSITIVE_ENV_PATTERN.sub(
            lambda match: f"{match.group(1)}={REDACTED_VALUE}",
            partially,
        )


def _redact_tokens(tokens: list[str]) -> list[str]:
    redacted: list[str] = []
    idx = 0

    while idx < len(tokens):
        token = tokens[idx]

        if token.startswith("--") and "=" in token:
            flag, value = token.split("=", 1)
            if _is_sensitive_key(flag):
                redacted.append(f"{flag}={REDACTED_VALUE}")
            else:
                redacted.append(_redact_token_assignment(token, default_value=value))
            idx += 1
            continue

        if token.startswith("--") and _is_sensitive_key(token):
            redacted.append(token)
            if idx + 1 < len(tokens):
                redacted.append(REDACTED_VALUE)
                idx += 2
            else:
                idx += 1
            continue

        redacted.append(_redact_token_assignment(token))
        idx += 1

    return redacted


def _redact_token_assignment(token: str, default_value: str | None = None) -> str:
    if "=" not in token:
        return token

    key, value = token.split("=", 1)
    if _is_sensitive_key(key):
        return f"{key}={REDACTED_VALUE}"

    if default_value is not None and _is_sensitive_key(value):
        return f"{key}={REDACTED_VALUE}"
    return token
