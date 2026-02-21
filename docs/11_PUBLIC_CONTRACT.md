<<<<<<< HEAD
# Public Contract 📜🖤

This is the law.

TaskX is not a suggestion engine.
It is a deterministic execution kernel.

If we violate this, it's a bug.
If we change this, it's a version bump.

No quiet drift. No soft reinterpretation. 😈

---

## Article I — The Packet Is Sovereign 👑

The packet is the only authoritative input.

TaskX will not infer intent.
TaskX will not assume context.
TaskX will not "helpfully interpret."

If it's not declared, it does not exist. 🔒

---

## Article II — Determinism Is Absolute 🔥

For identical:
- packet
- declared environment inputs
- TaskX version

Outputs must be byte-identical:
- artifacts
- exit codes
- route plans

If it changes unexpectedly, that's a contract violation. 🧾

---

## Article III — Refusal Over Deception 💄

TaskX refuses before it guesses.

If:
- validation fails
- policy is violated
- a runner is unavailable
- required inputs are missing

Then TaskX emits a refusal artifact.

Refusal is not failure.
Refusal is integrity. 🖤

---

## Article IV — One Path Per Invocation ⚔️

One invocation.
One route.
One outcome.

No silent fallback.
No backup plan.
No sneaky second attempt.

If you want orchestration, build it outside the kernel. 😈

---

## Article V — Artifact Primacy 🧾

Artifacts are truth.

Console output is theater.
Artifacts are receipts.

Every invocation must produce canonical artifacts.
If artifacts are missing or inconsistent, the run is invalid. 🔥

---

## Article VI — No Hidden Behavior 🚫

TaskX will never:
- retry without instruction
- execute multiple runners
- persist cross-run state
- perform undeclared network calls
- mutate repository state implicitly

If it does, the contract is broken. Period. 🧨

---

## Article VII — Version Discipline 💋

Semantic Versioning, enforced with honor:

- Patch: internal correction
- Minor: additive change
- Major: contract alteration

If determinism shifts, the version shifts.
No quiet drift. No secret edits. 🧾

---

## Final Clause 🖤

TaskX is not here to be convenient.

It's here to be correct.

Correctness is the only acceptable kind of "danger."
=======
# Public Contract

This document defines TaskX's public, user-visible contract: inputs, outputs, determinism, exit codes, and non-goals.

## Inputs

- Task Packet: see `13_TASK_PACKET_FORMAT.md`
- Route availability config: `.taskx/runtime/availability.yaml`

## Outputs

TaskX writes deterministic artifacts for a given invocation:

- Route plan artifacts under `out/taskx_route/`
- Refusal reasons when refusing

Console output is informational. Artifacts are the record.

## Determinism rules

For identical:

- Packet
- Declared inputs
- TaskX version

Outputs must be byte-stable unless explicitly documented otherwise.

## Exit codes

- `0`: success
- `2`: refusal (contractual non-execution)
- `1`: error (unexpected failure)

## Non-goals

- Implicit retries and fallback runners
- Undeclared network access
- Cross-run mutable state

## Versioning policy

TaskX follows Semantic Versioning.

- Patch: bug fixes only
- Minor: additive and backward-compatible
- Major: contract-breaking

>>>>>>> codex/TP-DOCS-STRUCTURE-0002-doc-spine
