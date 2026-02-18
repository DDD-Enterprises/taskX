# Contributing

TaskX contributions must be deterministic, scoped, and evidence-backed.

## Setup

We use `uv`.

```bash
uv sync
uv run pytest
```

## Branch Discipline

- Start from a clean tree.
- Use a new branch or a worktree attached to a new branch.
- Keep changes inside packet scope.

## Pull Request Requirements

Every PR must include:
- clear scope
- determinism impact statement
- artifact impact statement
- proof bundle command output
- test results (`uv run pytest`)

We merge evidence.
