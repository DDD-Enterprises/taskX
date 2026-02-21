# Project Doctor

<<<<<<< HEAD
Audience: Maintainers
Status: Diagnostic Control Layer

The Doctor does not comfort you.

The Doctor inspects.
The Doctor diagnoses.
The Doctor reports.

And if something is wrong, the Doctor does not whisper.

---

## What the Doctor Checks

- Instruction block integrity
- Duplicate operator markers
- Configuration drift
- Missing required files
- Structural contradictions

It does not "fix" silently.
It does not "helpfully correct."

It observes.
It reports.
It exits with intent.

---

## Exit Codes

- PASS -> 0
- WARN -> 0
- FAIL -> non-zero (stable, deterministic)

FAIL does not mean chaos.
FAIL means: "Not acceptable."

---

## Export Behavior

By default, the Doctor exports diagnostic artifacts.

Even on FAIL.

Why?
Because evidence matters.
Silence is not discipline.

If you disable export, you are opting out of receipts.

---

## What the Doctor Will Never Do

- modify packet execution behavior
- retry validation
- silently rewrite files
- mask conflicts
- introduce nondeterminism

The Doctor does not negotiate with entropy.

---

## Philosophy

The Doctor does not shame you.

But it will absolutely document your mistakes.
=======
The project doctor inspects a repository and reports integrity status. It does not mutate project state.

## PASS/WARN/FAIL semantics

- PASS: exit `0`
- WARN: exit `0` (diagnostic warnings)
- FAIL: non-zero exit (stable)

## What doctor checks

- Project mode and identity rails
- Expected file layout for the selected mode
- Config consistency

## What doctor never does

- It never mutates packet execution behavior.
- It never modifies repository files unless explicitly running a fix mode.

## Operator prompt export policy (Policy A)

Note: `taskx ops doctor` exports the operator prompt by default unless `--no-export` is set.

This export does not affect packet routing or execution behavior. It exists to make operator context observable.

See also:

- Router: `12_ROUTER.md`
- Architecture: `10_ARCHITECTURE.md`
>>>>>>> codex/TP-DOCS-STRUCTURE-0002-doc-spine
