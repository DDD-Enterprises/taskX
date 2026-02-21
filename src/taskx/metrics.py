"""Local-only, opt-in CLI metrics for TaskX."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

METRICS_ENV_VAR = "TASKX_METRICS"
XDG_STATE_HOME_ENV_VAR = "XDG_STATE_HOME"
_STATE_FALLBACK = Path(".local") / "state"
_METRICS_RELATIVE_PATH = Path("taskx") / "metrics.json"


def _default_payload() -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "enabled": False,
        "commands": {},
    }


def _truthy(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def resolve_metrics_path(
    *,
    env: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> Path:
    """Return the canonical metrics file path."""
    effective_env = env if env is not None else {}
    xdg_state_home = effective_env.get(XDG_STATE_HOME_ENV_VAR)
    if xdg_state_home:
        base = Path(xdg_state_home).expanduser()
    else:
        base = (home if home is not None else Path.home()) / _STATE_FALLBACK
    return (base / _METRICS_RELATIVE_PATH).resolve()


def load_metrics(path: Path) -> dict[str, Any]:
    """Load metrics payload from disk, returning defaults on missing/invalid content."""
    payload = _default_payload()
    if not path.exists():
        return payload

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return payload

    if not isinstance(raw, dict):
        return payload

    enabled = raw.get("enabled")
    commands = raw.get("commands")

    payload["enabled"] = bool(enabled) if isinstance(enabled, bool) else False

    normalized_commands: dict[str, int] = {}
    if isinstance(commands, dict):
        for key, value in commands.items():
            if not isinstance(key, str):
                continue
            if isinstance(value, int) and value >= 0:
                normalized_commands[key] = value
    payload["commands"] = normalized_commands
    return payload


def save_metrics(path: Path, payload: dict[str, Any]) -> None:
    """Persist metrics payload atomically."""
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(payload, indent=2, sort_keys=True) + "\n"

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        delete=False,
        prefix=f".{path.name}.",
        suffix=".tmp",
    ) as tmp_file:
        tmp_file.write(serialized)
        tmp_path = Path(tmp_file.name)

    tmp_path.replace(path)


def metrics_env_enabled(env: Mapping[str, str] | None = None) -> bool:
    """Return whether metrics are enabled by environment variable."""
    effective_env = env if env is not None else {}
    return _truthy(effective_env.get(METRICS_ENV_VAR))


def metrics_effective_enabled(path: Path, env: Mapping[str, str] | None = None) -> bool:
    """Return true when either env or persistent opt-in enables metrics."""
    payload = load_metrics(path)
    persistent_enabled = bool(payload.get("enabled", False))
    return metrics_env_enabled(env) or persistent_enabled


def set_metrics_enabled(path: Path, enabled: bool) -> dict[str, Any]:
    """Set persistent opt-in status."""
    payload = load_metrics(path)
    payload["enabled"] = enabled
    save_metrics(path, payload)
    return payload


def reset_metrics(path: Path) -> dict[str, Any]:
    """Reset command counters while preserving opt-in status."""
    payload = load_metrics(path)
    payload["commands"] = {}
    save_metrics(path, payload)
    return payload


def infer_command_name(argv: Sequence[str]) -> str:
    """Infer a stable command key from argv for local counting."""
    if len(argv) <= 1:
        return "taskx"

    tokens = list(argv[1:])

    if any(token in {"--help", "-h"} for token in tokens):
        return "--help"

    if "--version" in tokens or tokens[0] == "version":
        return "--version"

    names: list[str] = []
    for token in tokens:
        if token.startswith("-"):
            if names:
                break
            continue
        names.append(token)
        if len(names) >= 2:
            break

    if not names:
        return "taskx"
    return " ".join(names)


def record_cli_invocation(
    *,
    argv: Sequence[str],
    path: Path,
    env: Mapping[str, str] | None = None,
) -> bool:
    """Record a CLI invocation when metrics are enabled."""
    if not metrics_effective_enabled(path, env):
        return False

    payload = load_metrics(path)
    commands = payload.get("commands", {})
    if not isinstance(commands, dict):
        commands = {}

    command_name = infer_command_name(argv)
    current_value = commands.get(command_name, 0)
    if not isinstance(current_value, int):
        current_value = 0
    commands[command_name] = current_value + 1
    payload["commands"] = commands
    save_metrics(path, payload)
    return True
