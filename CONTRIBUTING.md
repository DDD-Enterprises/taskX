# Contributing 💅⚙️

Welcome to the velvet rope.

If you want to make TaskX "friendlier" by adding ambiguity, retries, or silent fallback,
this is not that party.

If you want to make it sharper, more deterministic, more auditable:
come in. 🖤

---

## Setup 🧠

We use `uv`.

```bash
uv lock
uv sync
uv run pytest
```

Only uv workflows are supported in this repository.

---

## Branch Discipline 🧾

Start clean. Stay clean.

Work must be isolated in:
- a new branch, or
- a worktree attached to a new branch (preferred)

If you can't prove what changed, it didn't happen. 😈

---

## Determinism Is Sacred 🔥

Before you submit a PR, ask yourself:
- Did I introduce hidden behavior?
- Did I add fallback logic?
- Did I sneak in a retry?
- Did I make the kernel guess?
- Did I touch artifact formats or schema?

If yes: justify it with evidence and contract impact. 🧾🧨

---

## PR Requirements 🖤

Every PR must include:
- scope boundary (what changed / what did not)
- determinism impact statement
- artifact impact statement
- proof bundle (commands + outputs)
- `uv run pytest` results

We merge evidence.
We reject vibes. 💋

---

## Hard Limits 🚫

TaskX will never:
- retry automatically
- execute multiple runners per invocation
- persist cross-run state
- perform undeclared network calls
- guess user intent
- silently mutate repositories

Keep it explicit.
Keep it observable.
Keep it honest. 🧾
