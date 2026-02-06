"""Shared helpers for project init and directive pack toggles."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

try:
    from importlib.resources import files
except ImportError as exc:  # pragma: no cover - python<3.11 unsupported
    raise RuntimeError("TaskX requires Python 3.11+ for template loading.") from exc


MANAGED_FILES: tuple[str, ...] = (
    "PROJECT_INSTRUCTIONS.md",
    "CLAUDE.md",
    "CODEX.md",
    "AGENTS.md",
)

MANAGED_TEMPLATE_FILES: dict[str, str] = {
    "PROJECT_INSTRUCTIONS.md": "PROJECT_INSTRUCTIONS.template.md",
    "CLAUDE.md": "CLAUDE.template.md",
    "CODEX.md": "CODEX.template.md",
    "AGENTS.md": "AGENTS.template.md",
}

PACK_TEMPLATE_FILES: dict[str, str] = {
    "taskx": "directive_pack_taskx.md",
    "chatx": "directive_pack_chatx.md",
}

PACK_ORDER: tuple[str, ...] = ("taskx", "chatx")

SENTINELS: dict[str, tuple[str, str]] = {
    "taskx": ("<!-- TASKX:BEGIN -->", "<!-- TASKX:END -->"),
    "chatx": ("<!-- CHATX:BEGIN -->", "<!-- CHATX:END -->"),
}

DISABLED_TEXT = "(disabled)"

BUNDLE_FILE = "taskx_bundle.yaml"
BUNDLE_TEMPLATE_FILE = "taskx_bundle.template.yaml"

_ASSETS_PACKAGE = "taskx.assets.templates"


@dataclass(frozen=True)
class BlockUpdate:
    """Metadata for an applied sentinel block update."""

    block_added: bool
    content_changed: bool


def read_template_text(template_name: str) -> str:
    """Load template text from packaged assets."""
    try:
        template_file = files(_ASSETS_PACKAGE) / template_name
        return template_file.read_text(encoding="utf-8")
    except (FileNotFoundError, ModuleNotFoundError) as exc:
        raise KeyError(f"Template asset not found: {template_name}") from exc


def read_pack_text(pack_name: str) -> str:
    """Load canonical directive pack text by pack name."""
    if pack_name not in PACK_TEMPLATE_FILES:
        raise ValueError(f"Unsupported directive pack: {pack_name}")
    return read_template_text(PACK_TEMPLATE_FILES[pack_name]).strip()


def file_hash(text: str) -> str:
    """Return a deterministic hash for report diffing."""
    return sha256(text.encode("utf-8")).hexdigest()


def extract_block_content(text: str, pack_name: str) -> str | None:
    """Extract current content inside a sentinel block."""
    begin_marker, end_marker = get_sentinels(pack_name)
    lines = text.splitlines()
    block = _locate_block(lines, begin_marker, end_marker)
    if block is None:
        return None

    begin_idx, end_idx = block
    return "\n".join(lines[begin_idx + 1 : end_idx]).strip()


def apply_block_content(text: str, pack_name: str, content: str) -> tuple[str, BlockUpdate]:
    """Ensure sentinel block exists and replace only content inside it."""
    begin_marker, end_marker = get_sentinels(pack_name)
    lines = text.splitlines()
    payload_lines = content.splitlines() if content else []
    block = _locate_block(lines, begin_marker, end_marker)

    if block is None:
        updated_lines = lines[:]
        if updated_lines and updated_lines[-1].strip():
            updated_lines.append("")
        updated_lines.append(begin_marker)
        updated_lines.extend(payload_lines)
        updated_lines.append(end_marker)
        return _join_lines(updated_lines), BlockUpdate(block_added=True, content_changed=True)

    begin_idx, end_idx = block
    current_payload = lines[begin_idx + 1 : end_idx]
    if current_payload == payload_lines:
        return text, BlockUpdate(block_added=False, content_changed=False)

    updated_lines = lines[: begin_idx + 1] + payload_lines + lines[end_idx:]
    return _join_lines(updated_lines), BlockUpdate(block_added=False, content_changed=True)


def apply_pack_map(text: str, pack_content: dict[str, str]) -> tuple[str, dict[str, BlockUpdate]]:
    """Apply content updates for multiple packs in deterministic order."""
    updated_text = text
    updates: dict[str, BlockUpdate] = {}
    for pack_name in PACK_ORDER:
        if pack_name not in pack_content:
            continue
        updated_text, update = apply_block_content(updated_text, pack_name, pack_content[pack_name])
        updates[pack_name] = update
    return updated_text, updates


def is_enabled_content(content: str | None) -> bool:
    """Return True when block content represents an enabled pack."""
    if content is None:
        return False
    normalized = content.strip()
    return bool(normalized) and normalized != DISABLED_TEXT


def get_sentinels(pack_name: str) -> tuple[str, str]:
    """Get begin/end sentinel markers for a pack name."""
    if pack_name not in SENTINELS:
        raise ValueError(f"Unsupported directive pack: {pack_name}")
    return SENTINELS[pack_name]


def _locate_block(lines: list[str], begin_marker: str, end_marker: str) -> tuple[int, int] | None:
    """Find begin/end marker indices for a block, if present."""
    begin_idx: int | None = None
    for idx, line in enumerate(lines):
        if begin_idx is None:
            if line.strip() == begin_marker:
                begin_idx = idx
            continue
        if line.strip() == end_marker:
            return begin_idx, idx
    return None


def _join_lines(lines: list[str]) -> str:
    """Join file lines with a trailing newline for deterministic output."""
    if not lines:
        return ""
    return "\n".join(lines).rstrip("\n") + "\n"

