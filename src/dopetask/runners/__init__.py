"""Runner adapters for TaskX orchestrator."""

from dopetask.runners.base import RunnerAdapter
from dopetask.runners.claude_code import ClaudeCodeAdapter
from dopetask.runners.codex_cli import CodexCliAdapter
from dopetask.runners.copilot_cli import CopilotCliAdapter
from dopetask.runners.google_jules import GoogleJulesAdapter

RUNNER_ADAPTERS: dict[str, type[RunnerAdapter]] = {
    "claude_code": ClaudeCodeAdapter,
    "codex_desktop": CodexCliAdapter,
    "copilot_cli": CopilotCliAdapter,
    "google_jules": GoogleJulesAdapter,
}

__all__ = [
    "RunnerAdapter",
    "ClaudeCodeAdapter",
    "CodexCliAdapter",
    "CopilotCliAdapter",
    "GoogleJulesAdapter",
    "RUNNER_ADAPTERS",
]
