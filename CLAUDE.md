# CLAUDE.md — Evergreen Project Memory (Dopemux-Compatible)

Evergreen: DO NOT edit per task. Task packets change; this file stays stable.

<!-- TASKX_TP_GIT_WORKFLOW_START -->
## Mandatory Git Workflow for All Task Packets (dopeTask)

- Never work directly on `main`. `main` must remain clean.
- Stashes are forbidden. If `git stash list` is non-empty, STOP and clean it.
- Every TP must use a dedicated worktree + branch created by dopeTask:
  - `dopetask tp git doctor`
  - `dopetask tp git start <TP_ID> <slug>`
- Work must be performed inside `.worktrees/<TP_ID>`.
- Commits must follow the TP’s commit plan.
- Integration must happen via PR:
  - `dopetask tp git pr <TP_ID> --title "TP-XXXX: ..." --body-file ...`
  - `dopetask tp git merge <TP_ID>` (auto-merge when available; fail-closed otherwise)
- After merge (confirmed), sync and cleanup:
  - `dopetask tp git sync-main`
  - `dopetask tp git cleanup <TP_ID>`

### One-command mode (preferred)
Use:
- `dopetask tp run <TP_ID> <slug> [--test-cmd "..."] [--wait-merge]`

This command must emit a proof pack under `runs/tp/...` and must not claim merge/cleanup success unless verified.
<!-- TASKX_TP_GIT_WORKFLOW_END -->

## 0) Prime rule
TASK PACKETS ARE LAW.
If no task packet is provided: STOP and ask for it.

## 1) PLAN vs ACT mode (binding)
PLAN mode:
- Focus on architecture, tradeoffs, and clean breakdowns (max 3 options when needed).
- Use the Dopemux toolchain for design decisions; log decisions to ConPort.

ACT mode:
- Make minimal diffs that satisfy the task packet.
- Use codebase context tools before editing; run verification before claiming "done."

## 2) Attention-state adaptive output (binding defaults)
If unsure, assume "focused."
- scattered: concise, one next action
- focused: structured, up to 3 prioritized actions
- hyperfocus: comprehensive, full plan + deeper verification

(These defaults are consistent with your mode/attention routing docs.)

## 3) Quick Start Commands

### Development Setup
```bash
# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Install git hooks
scripts/install-git-hooks.sh
```

### Build & Test
```bash
# Run tests with coverage (configured in pyproject.toml)
pytest

# Type checking
mypy src/

# Linting
ruff check .

# Format check
ruff format --check .

# Build distribution packages
python -m build
# or
scripts/dopetask_build.sh
```

### dopeTask CLI Usage
```bash
# Diagnostic health check
dopetask doctor

# Basic task lifecycle
dopetask compile-tasks --mode mvp --max-packets 5
dopetask run-task --task-id T001
dopetask gate-allowlist --run ./out/runs/RUN_..._T001
dopetask promote-run --run ./out/runs/RUN_..._T001

# Dopemux namespace (auto-discovery)
dopetask dopemux compile
dopetask dopemux run --task-id T002
dopetask dopemux gate
```

## 4) Project Structure

```
src/dopetask/          # Core task packet engine
├── cli.py          # Main CLI entry point (Typer-based)
├── doctor.py       # Diagnostic tool implementation
├── ci_gate.py      # Allowlist gate checking
├── pipeline/       # Task compilation, execution, promotion
└── project/        # Project initialization and mode management

src/dopetask_adapters/ # Dopemux integration
└── dopemux.py      # Auto-discovery of Dopemux paths

dopetask_schemas/      # JSON schemas packaged with distribution
schemas/            # Schema definitions for validation

scripts/            # Build and installation automation
├── dopetask_build.sh          # Build sdist + wheel
├── install-git-hooks.sh    # Install pre-commit hooks
└── dopetask_install_into_repo.sh  # Install dopeTask into other repos

docs/               # User documentation
├── INSTALL.md      # Installation guide
├── RELEASE.md      # Release process
└── PROJECT_DOCTOR.md  # Doctor tool documentation
```

## 5) Dopemux workflow defaults

RESEARCH:
- Use dope-context for in-repo code examples and patterns.

DESIGN:
- Log all meaningful decisions to ConPort with log_decision.

IMPLEMENTATION:
- Use serena-v2 + dope-context FIRST to locate code and patterns.
- Log progress to ConPort as work advances.

REVIEW / COMMIT:
- Run `pre-commit run --all-files` before commit.
- Update ConPort progress to DONE (or current status).

## 6) Coding + testing norms (repo-generic defaults)
- Match existing conventions first.
- New behavior must have tests (unit for logic; integration when behavior spans stages).
- Never claim tests passed unless you ran them; otherwise say "not run" and why.
- All functions must be typed (mypy --strict enforcement).

## 7) Key Files

- `pyproject.toml` - Project metadata, dependencies, tool configuration (Hatchling build, Ruff lint, pytest, mypy)
- `DOPETASK_VERSION.lock` - Version pinning for deterministic builds
- `.dopetaskroot` - Marks dopeTask project root
- `dopetask_bundle.yaml` - Task bundle configuration
- `README.md` - User-facing project overview and quick start

## 8) Development Gotchas

- **Deterministic time**: dopeTask mocks `datetime.now()` for reproducible builds
- **Allowlist enforcement**: Gate rejects any file changes not in allowlist
- **Offline-first design**: All dependencies must be pre-installed; no network access during runs
- **Strict typing**: Project uses `mypy --strict` - all functions must be typed
- **Test coverage**: pytest configured to fail under 1% coverage (see pyproject.toml line 132)
- **Pre-commit required**: Changes must pass `pre-commit run --all-files` before commit
- **No `datetime.now()`**: Use `timestamp_mode="deterministic"` for release builds
- **Token-gated commits**: Cannot commit without a promotion token from gate-allowlist pass

## 9) New Command Surfaces

- `dopetask project shell init|status`
- `dopetask project upgrade`
- `dopetask route init|plan|handoff|explain`
- `dopetask pr open`

Branch restore contract:
- If a dopeTask command switches branches, it must restore original branch/HEAD unless explicitly disabled.

## 10) Response format (mandatory)
A) MODE + attention state
B) PLAN
C) CHANGES
D) COMMANDS RUN + RESULTS
E) CONPORT LOGGING
F) NEXT ACTION or CHECKPOINT STOP

<!-- DOPETASK:AUTOGEN:START -->
## dopeTask Command Surface (Autogenerated)

### Command Tree
- dopetask bundle
  - dopetask bundle export
  - dopetask bundle ingest
- dopetask case
  - dopetask case audit
- dopetask ci-gate
- dopetask collect-evidence
- dopetask commit-run
- dopetask commit-sequence
- dopetask compile-tasks
- dopetask docs
  - dopetask docs refresh-llm
- dopetask doctor
- dopetask dopemux
  - dopetask dopemux collect
  - dopetask dopemux compile
  - dopetask dopemux feedback
  - dopetask dopemux gate
  - dopetask dopemux loop
  - dopetask dopemux promote
  - dopetask dopemux run
- dopetask finish
- dopetask gate-allowlist
- dopetask loop
- dopetask manifest
  - dopetask manifest check
  - dopetask manifest finalize
  - dopetask manifest init
- dopetask orchestrate
- dopetask pr
  - dopetask pr open
- dopetask project
  - dopetask project disable
  - dopetask project doctor
  - dopetask project enable
  - dopetask project init
  - dopetask project mode
    - dopetask project mode set
  - dopetask project shell
    - dopetask project shell init
    - dopetask project shell status
  - dopetask project status
  - dopetask project upgrade
- dopetask promote-run
- dopetask route
  - dopetask route explain
  - dopetask route handoff
  - dopetask route init
  - dopetask route plan
- dopetask run-task
- dopetask spec-feedback
- dopetask wt
  - dopetask wt start

### Assisted Routing (dopetask route)
- Config: `.dopetask/runtime/availability.yaml`
- Artifacts:
  - `out/dopetask_route/ROUTE_PLAN.json`
  - `out/dopetask_route/ROUTE_PLAN.md`
  - `out/dopetask_route/HANDOFF.md`
- Execution: assisted-only (prints handoffs; does not invoke external runners)

### Availability Summary (deterministic)
- Available runners: claude_code, codex_desktop, copilot_cli
- Available models: gpt-5.1-mini, gpt-5.2, gpt-5.3-codex, haiku-4.5, sonnet-4.55
- Policy:
  - max_cost_tier: high
  - min_total_score: 50
  - stop_on_ambiguity: True
  - escalation_ladder: [gpt-5.1-mini, haiku-4.5, sonnet-4.55, gpt-5.3-codex]

### Minimal schema (snippet, stable)
```yaml
models:
  gpt-5.1-mini:
    strengths: [cheap]
    cost_tier: cheap
    context: medium
runners:
  claude_code:
    available: true
    strengths: [code_edit]
policy:
  max_cost_tier: high
  min_total_score: 50
  stop_on_ambiguity: True
  escalation_ladder: [gpt-5.1-mini, haiku-4.5, sonnet-4.55, gpt-5.3-codex]
```

Generated by: dopetask docs refresh-llm
<!-- DOPETASK:AUTOGEN:END -->

<!-- TASKX:BEGIN operator_system v=1 platform=chatgpt model=gpt-5.2-thinking hash=8b84e46d1c68ff884983949ec74f9f7aa98b9d4318d3f91055f8852d24eae8da -->
# OPERATOR SYSTEM PROMPT
# Project: dopeTask
# Platform: chatgpt
# Model: gpt-5.2-thinking
# Repo Root: /Users/hue/code/dopeTask
# Timezone: America/Vancouver
# dopeTask Pin: git_commit=50548e9c079fb86245d8580f25cf7d11485be528
# CLI Min Version: 0.1.2

# BASE SUPERVISOR (Canonical Minimal Baseline v1)

## Role

You are the Supervisor / Auditor.

You:
- Author Task Packets.
- Enforce invariants.
- Audit implementer output.
- Protect determinism and auditability.

You are NOT:
- The implementer.
- A runtime generator.
- A copywriter.

## Authority Hierarchy (Highest -> Lowest)

1. Active Task Packet
2. Repository code and tests
3. Explicit schemas and formal contracts
4. Versioned project docs
5. Existing implementation
6. Model heuristics

If a conflict is detected:
- STOP.
- Surface the conflict explicitly.
- Do not auto-resolve.

## Non-Negotiables

- Task Packets are law.
- No fabrication.
- If evidence is missing -> mark UNKNOWN and request specific file/output.
- Prefer minimal diffs.
- Determinism over cleverness.
- Every change must be auditable.

## Determinism Contract

- Same inputs -> same outputs.
- No hidden randomness.
- No time-based logic unless explicitly allowed.
- Outputs must be reproducible.

## Output Discipline

Unless specified otherwise, responses must be one of:

- Design Spec
- Task Packet
- Patch Instructions
- Audit Report

Never mix formats.

# LAB BOUNDARY (Canonical Minimal Baseline v1)

## Project Context

You are operating inside a Development & Architecture Lab.

This lab:
- Designs systems.
- Defines prompts, rules, schemas, and invariants.
- Audits correctness and failure modes.

This lab does NOT:
- Act as live production runtime.
- Optimize for persuasion or conversion unless explicitly marked as test output.
- Generate final production artifacts unless instructed.

## Mode Discipline

If user intent is unclear:
- Ask for clarification.
- Do not guess.

If asked to perform runtime behavior inside lab mode:
- Pause and confirm whether this is lab testing or production generation.

## Correctness Priority

When forced to choose:
- Correctness over speed.
- Clarity over cleverness.
- Explicit contracts over implicit behavior.

# chatgpt Overlay
Specifics for chatgpt


## Handoff contract
- Follow all instructions provided in this prompt.
- Use dopeTask CLI for all task management.
- Ensure all outputs conform to the project spec.

<!-- TASKX:END operator_system -->
