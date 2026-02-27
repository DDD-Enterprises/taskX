"""Marker-scoped LLM refresh helpers for CLAUDE.md and AGENTS.md."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING, Any

from dopetask.guard.identity import RepoIdentity, load_repo_identity

if TYPE_CHECKING:
    from pathlib import Path

AUTOGEN_START = "<!-- DOPETASK:AUTOGEN:START -->"
AUTOGEN_END = "<!-- DOPETASK:AUTOGEN:END -->"
AUTOGEN_HINT = "<!-- (managed by dopetask docs refresh-llm) -->"



def ensure_autogen_markers(
    path: Path,
    *,
    start: str = AUTOGEN_START,
    end: str = AUTOGEN_END,
) -> None:
    """Ensure an autogen marker block exists in a markdown file."""
    text = path.read_text(encoding="utf-8") if path.exists() else ""

    if start in text and end in text:
        return

    block = f"{start}\n{AUTOGEN_HINT}\n{end}\n"
    if not text:
        updated = block
    else:
        normalized = text
        if not normalized.endswith("\n"):
            normalized += "\n"
        updated = f"{normalized.rstrip()}\n\n{block}"

    path.write_text(updated, encoding="utf-8")



def replace_autogen_block(
    path: Path,
    content: str,
    *,
    start: str = AUTOGEN_START,
    end: str = AUTOGEN_END,
) -> None:
    """Replace only the content between autogen markers."""
    text = path.read_text(encoding="utf-8")
    start_index = text.find(start)
    if start_index < 0:
        raise RuntimeError(f"Missing start marker in {path}")

    end_index = text.find(end, start_index + len(start))
    if end_index < 0:
        raise RuntimeError(f"Missing end marker in {path}")

    prefix = text[:start_index]
    suffix = text[end_index + len(end):]

    stripped = content.strip("\n")
    middle = f"\n{stripped}\n" if stripped else "\n"

    updated = f"{prefix}{start}{middle}{end}{suffix}"
    path.write_text(updated, encoding="utf-8")



def build_llm_prompt(repo_identity: RepoIdentity | None, repo_scan: dict[str, Any]) -> str:
    """Build deterministic prompt requesting only autogen markdown content."""
    project_id = repo_identity.project_id if repo_identity is not None else "unknown"
    project_slug = repo_identity.project_slug if repo_identity is not None else "unknown"
    scan_lines = "\n".join(f"- {key}: {value}" for key, value in sorted(repo_scan.items()))

    return (
        "You are refreshing dopeTask instruction-file AUTOGEN sections.\n"
        "Return ONLY markdown content intended for insertion between markers.\n"
        "Do not include marker lines, YAML, JSON, or code fences unless needed as markdown examples.\n\n"
        f"Repo project_id: {project_id}\n"
        f"Repo slug: {project_slug}\n"
        "Repo scan:\n"
        f"{scan_lines}\n\n"
        "Content goals:\n"
        "- Keep directives concise and actionable.\n"
        "- Include current project identity and guard expectations.\n"
        "- Preserve deterministic, safety-first language.\n"
    )



def run_tool_cmd(tool_cmd: list[str], stdin: str) -> str:
    """Run external tool command, providing prompt via stdin and returning stdout."""
    if not tool_cmd:
        raise RuntimeError("tool_cmd must not be empty")

    result = subprocess.run(
        tool_cmd,
        input=stdin,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        details = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(
            f"LLM refresh command failed ({result.returncode}): {details}"
        )
    return result.stdout



def refresh_llm_docs(
    repo_root: Path,
    tool_cmd: list[str],
    user_profile: str,
    apply: bool = True,
) -> dict[str, Any]:
    """Refresh AUTOGEN blocks in CLAUDE.md and AGENTS.md."""
    repo_root = repo_root.resolve()

    try:
        repo_identity = load_repo_identity(repo_root)
    except RuntimeError as exc:
        if str(exc).startswith("Repo identity file not found:"):
            repo_identity = None
        else:
            raise

    target_paths = [repo_root / "CLAUDE.md", repo_root / "AGENTS.md"]
    if apply:
        for path in target_paths:
            ensure_autogen_markers(path)

    repo_scan: dict[str, Any] = {
        "user_profile": user_profile,
        "targets": ", ".join(path.name for path in target_paths),
    }
    prompt = build_llm_prompt(repo_identity, repo_scan)
    generated = run_tool_cmd(tool_cmd, prompt)
    generated_content = generated.strip()

    if apply:
        for path in target_paths:
            replace_autogen_block(path, generated_content)

    return {
        "repo_root": str(repo_root),
        "apply": apply,
        "files": [str(path) for path in target_paths],
        "generated_content": generated_content,
    }
