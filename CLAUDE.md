# CLAUDE.md — Evergreen Project Memory (Dopemux-Compatible)

Evergreen: DO NOT edit per task. Task packets change; this file stays stable.

## 0) Prime rule
TASK PACKETS ARE LAW.
If no task packet is provided: STOP and ask for it.

## 1) PLAN vs ACT mode (binding)
PLAN mode:
- Focus on architecture, tradeoffs, and clean breakdowns (max 3 options when needed).
- Use the Dopemux toolchain for design decisions; log decisions to ConPort.

ACT mode:
- Make minimal diffs that satisfy the task packet.
- Use codebase context tools before editing; run verification before claiming “done.”

## 2) Attention-state adaptive output (binding defaults)
If unsure, assume “focused.”
- scattered: concise, one next action
- focused: structured, up to 3 prioritized actions
- hyperfocus: comprehensive, full plan + deeper verification

(These defaults are consistent with your mode/attention routing docs.) 

## 3) Dopemux workflow defaults (Context7 is retired)
RESEARCH:
- pal apilookup FIRST for authoritative library/API docs.
- Then dope-context for in-repo examples.

DESIGN:
- pal planner for design planning; pal consensus for tradeoffs.
- ConPort log_decision for any meaningful choice.

PLANNING:
- task-orchestrator FIRST for task breakdown (and optionally ticketing, if the task packet requires it).

IMPLEMENTATION:
- serena-v2 + dope-context FIRST to locate code and patterns.
- pal apilookup for API certainty; pal thinkdeep for hard problems.
- ConPort log_progress as work advances.

REVIEW / COMMIT:
- pal codereviewer before commit; pal secaudit for security-sensitive changes.
- pre-commit run --all-files before commit.
- Update ConPort progress to DONE (or current status).

## 4) Coding + testing norms (repo-generic defaults)
- Match existing conventions first.
- New behavior must have tests (unit for logic; integration when behavior spans stages).
- Never claim tests passed unless you ran them; otherwise say “not run” and why.

## 5) Response format (mandatory)
A) MODE + attention state
B) PLAN
C) CHANGES
D) COMMANDS RUN + RESULTS
E) CONPORT LOGGING
F) NEXT ACTION or CHECKPOINT STOP