#!/usr/bin/env python3
"""Wrapper script for TaskX LLM docs refresh."""

from __future__ import annotations

import argparse
import shlex
from pathlib import Path

from dopetask.docs.llm_refresh import refresh_llm_docs



def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh CLAUDE.md and AGENTS.md AUTOGEN blocks")
    parser.add_argument("--tool-cmd", required=True, help="Quoted tool command, e.g. 'echo \"# text\"'")
    parser.add_argument("--user-profile", required=True, help="User profile/context string")
    parser.add_argument("--repo-root", default=".", help="Repository root (default: current directory)")
    parser.add_argument("--apply", dest="apply", action="store_true", help="Apply file edits")
    parser.add_argument("--dry-run", dest="apply", action="store_false", help="Do not edit files")
    parser.set_defaults(apply=True)
    args = parser.parse_args()

    result = refresh_llm_docs(
        repo_root=Path(args.repo_root),
        tool_cmd=shlex.split(args.tool_cmd),
        user_profile=args.user_profile,
        apply=args.apply,
    )

    mode = "applied" if args.apply else "dry-run"
    print(f"refresh-llm {mode}: {', '.join(result['files'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
