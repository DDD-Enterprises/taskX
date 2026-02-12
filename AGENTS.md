# AGENTS.md — Evergreen Agent Entry Point (Dopemux-Compatible)

Evergreen: DO NOT edit per task. Task packets change; this file stays stable.

## 0) Prime rule
TASK PACKETS ARE LAW.
- Implement exactly what the active task packet requests.
- If a coding request arrives without a task packet: STOP and ask for it.

## 1) Dopemux operating mode
Use:
- PLAN mode for architecture/design/planning.
- ACT mode for implementation/refactors/tests/fixes.
Adapt verbosity to attention state: scattered / focused / hyperfocus. (See CLAUDE.md.)

## 2) Dopemux MCP workflow matrix (binding behavior)
Use the right tool for the phase:
- RESEARCH: pal apilookup FIRST for authoritative library/API docs (Context7 is retired).
- DESIGN: pal planner / pal consensus as needed; log decisions to ConPort.
- PLANNING: task-orchestrator FIRST for breakdown.
- IMPLEMENTATION: serena-v2 + dope-context FIRST for codebase context; apilookup for API certainty.
- REVIEW: pal codereviewer before commit; pal secaudit for security-sensitive changes.
- COMMIT: pre-commit run --all-files before committing; update ConPort progress.

(These defaults match the Dopemux workflow matrix and implicit rules.) 

## 3) ConPort logging is mandatory
- Any meaningful decision → ConPort log_decision (what/why/tradeoffs).
- Any progress update → ConPort log_progress / update_progress (status + next).

## 4) Coding conventions (repo-generic defaults)
Follow existing repo style first. If ambiguous:
- Python: type hints for new/changed public functions.
- Prefer small, testable functions; minimize side-effects.
- Errors: never swallow exceptions; fail with actionable messages.
- Logging: do not leak sensitive content.
- I/O: prefer atomic writes (temp → rename).
- Security: never commit secrets; redact before external calls.

## 5) Standard response format (mandatory, every response)
A) MODE: PLAN or ACT + attention state guess (scattered/focused/hyperfocus)
B) PLAN: 3–7 bullets
C) CHANGES: files touched (or “no changes”)
D) COMMANDS RUN + RESULTS (or “not run” + why)
E) CONPORT: what was logged / what must be logged
F) NEXT: one clear next action OR “CHECKPOINT STOP”

## 6) Hard stop conditions
Stop and ask if:
- Task packet is missing, ambiguous, or lacks an allowlist for edits.
- You’d need to invent requirements, data, or “best guesses.”
- Verification gates can’t be run or would be bypassed.
- Instructions conflict (task packet vs repo constraints): STOP and surface the conflict.

<!-- TASKX:AUTOGEN:START -->
<!-- (managed by taskx docs refresh-llm) -->
<!-- TASKX:AUTOGEN:END -->
