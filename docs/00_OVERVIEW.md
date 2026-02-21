<<<<<<< HEAD
# Overview ⚙️🖤

TaskX is a deterministic execution kernel.

It consumes packets.
It produces plans or refusals.
It executes **one** path.
It writes artifacts **every** time. 🧾

No silent fallbacks.
No "cute" retries.
No mind-reading.

If it didn't leave evidence, it didn't happen. 😈

---

## Why It Exists 🔥

Most automation tools are chaos goblins in a trench coat:

- They retry and pretend it's resilience.
- They "try something else" and call it helpful.
- They mutate state and act surprised when trust evaporates.

TaskX does not do improv.

TaskX does **discipline**:
- clarity over convenience
- refusal over deception
- artifacts over vibes

---

## Kernel vs Ecosystem 💅

TaskX is the execution spine, not the whole creature.

TaskX does **NOT**:
- schedule recurring jobs
- persist cross-run memory
- orchestrate multiple packets
- execute multiple runners
- retry automatically
- perform undeclared network calls
- mutate your repo behind your back

If you want orchestration, build it **above** the kernel.
The kernel stays tight. Tight stays trustworthy. 🖤

---

## Quick Start (Dev) 🧠⚡

We use `uv` because we like things fast and controlled.

```bash
uv sync
uv run pytest
uv run taskx --help
```

Only uv workflows are supported in this repository.

---

## The Law (Public Contract) 📜

Your guarantees live here:
- `docs/11_PUBLIC_CONTRACT.md`

If behavior changes, the version changes.
No silent drift. No quiet power moves. 🧾
=======
# Overview

TaskX is a deterministic execution kernel for task packets.

It is artifact-first and refusal-first:

- If it cannot proceed under declared policy, it refuses with evidence.
- If it did not write an artifact, it did not happen.

## Kernel vs ecosystem

The kernel:

- Validates inputs (task packets and declared config).
- Produces a deterministic plan or a deterministic refusal.
- Executes exactly one selected path in `auto` mode (or emits a handoff in `manual` mode).
- Writes canonical artifacts before exit.

The ecosystem may add scheduling, orchestration, UI, or memory. Those are intentionally out of scope for the kernel.

## Promises

- Deterministic planning and artifact writing for identical inputs and version.
- Stable refusal semantics with evidence.
- No hidden retries or fallback execution paths.

## Non-goals

- Being a general-purpose workflow engine.
- Implicit network access.
- Cross-run mutable state.

## Next

- Architecture: `10_ARCHITECTURE.md`
- Public contract: `11_PUBLIC_CONTRACT.md`
- Install: `01_INSTALL.md`
- Quickstart: `02_QUICKSTART.md`

>>>>>>> codex/TP-DOCS-STRUCTURE-0002-doc-spine
