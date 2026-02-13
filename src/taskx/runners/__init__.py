"""Runner adapters for TaskX orchestrator."""

from taskx.runners.base import RunnerAdapter
from taskx.runners.claude_code import ClaudeCodeAdapter
from taskx.runners.codex_cli import CodexCliAdapter
from taskx.runners.copilot_cli import CopilotCliAdapter

RUNNER_ADAPTERS: dict[str, type[RunnerAdapter]] = {
    "claude_code": ClaudeCodeAdapter,
    "codex_desktop": CodexCliAdapter,
    "copilot_cli": CopilotCliAdapter,
}

__all__ = [
    "RunnerAdapter",
    "ClaudeCodeAdapter",
    "CodexCliAdapter",
    "CopilotCliAdapter",
    "RUNNER_ADAPTERS",
]
