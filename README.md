# TaskX is a deterministic task-packet execution kernel that plans one path or refuses with evidence.

## Guarantees

- Artifact-first: if it did not write an artifact, it did not happen.
- Refusal-first: invalid or unsafe inputs produce a structured refusal with a stable exit code.
- Deterministic: identical packet + declared inputs + TaskX version yields identical outputs.
- Single-path: no hidden retries, no fallback runners, no background execution.

## Install

uv (recommended):

```bash
uv tool install taskx
taskx --help
```

pip:

```bash
python -m pip install taskx
taskx --help
```

See `docs/01_INSTALL.md` for developer workflows and testing.

## 60-second example

```bash
taskx route init --repo-root .
cat > PACKET.md <<'EOF'
# Packet
ROUTER_HINTS:
  risk: low
EOF
taskx route plan --repo-root . --packet PACKET.md
ls -1 out/taskx_route/
```

Expected outputs:

- `out/taskx_route/ROUTE_PLAN.json`
- `out/taskx_route/ROUTE_PLAN.md`
- `out/taskx_route/HANDOFF.md` (for handoff flows)

<<<<<<< HEAD
## Documentation Map

Canonical spine:

1. `docs/00_OVERVIEW.md`
2. `docs/10_ARCHITECTURE.md`
3. `docs/11_PUBLIC_CONTRACT.md`
4. `docs/12_ROUTER.md`
5. `docs/14_PROJECT_DOCTOR.md`
6. `docs/90_RELEASE.md`

Extended references:

- Install: `docs/01_INSTALL.md`
- Quickstart: `docs/02_QUICKSTART.md`
- Task packet format: `docs/13_TASK_PACKET_FORMAT.md`
- Worktrees and commit sequencing (maintainers): `docs/20_WORKTREES_COMMIT_SEQUENCING.md`
- Case bundles (maintainers): `docs/21_CASE_BUNDLES.md`
- Release (maintainers): `docs/90_RELEASE.md`
- Security policy: `SECURITY.md`
- Contributing guide: `CONTRIBUTING.md`

## Kernel vs ecosystem

TaskX (kernel) validates packets, plans deterministically, executes one path (or emits a manual handoff), and writes canonical artifacts.

Everything else (scheduling, orchestration, memory, UX) belongs in the ecosystem above the kernel.

## Badge wall

- Deterministic: identical packet + declared inputs + TaskX version yields identical outputs.
- Implicit Retries: no hidden retries.
- Silent Fallbacks: no fallback runners.
- Cross-Run State: no cross-run mutable state.
- Multi-Runner: one path only (single-path execution).
- Ghost Behavior: if it did not write an artifact, it did not happen.

## Kernel Manifesto

TaskX is strict by design:

- one packet, one scoped objective
- one path, or explicit refusal with evidence
- one artifact trail that can be verified end to end

The goal is operational trust, not convenience theater.

## Anti-Features

TaskX will never:
- retry silently
- fallback to a different runner
- execute multiple paths
- persist state across runs
- perform undeclared network calls
- "do what you meant"
- reorder declared steps
- mutate your repository implicitly

If you want flexibility, build it above the kernel.

## Kernel FAQ

**Why does TaskX refuse so often?**  
Because refusal protects determinism and keeps artifacts trustworthy.

**Why require proof bundles?**  
Because claims without command output are not verifiable.

**Why avoid background behavior?**  
Because state changes must remain explicit, local, and auditable.

## Determinism Stress Test

Given identical:
- packet
- declared environment inputs
- TaskX version

You must observe identical:
- route plans
- artifacts
- exit codes
- hashes

If any of those change without a version bump:
the contract has been violated.

## Why TaskX Is Hot

- **🔮 Deterministic Time Travel**: We mock time. Literal time. Your builds will produce the exact same artifacts today, tomorrow, and in 2050.
- **🛡️ The Great Allowlist**: Files don't just "change." They apply for a visa. Our `AllowlistDiff` system catches unauthorized mutations before they even think about becoming a commit.
- **🔌 Offline by Design**: TaskX assumes the internet is down. If your build needs `npm install` to run, go back to square one.
- **🧬 Audit Trails**: Every run produces a forensic verification trail. Who ran it? When? with what inputs? It's all in the JSON.
=======
## Docs

- Overview: `docs/00_OVERVIEW.md`
- Install: `docs/01_INSTALL.md`
- Quickstart: `docs/02_QUICKSTART.md`
- Architecture: `docs/10_ARCHITECTURE.md`
- Public contract: `docs/11_PUBLIC_CONTRACT.md`
- Router: `docs/12_ROUTER.md`
- Task packet format: `docs/13_TASK_PACKET_FORMAT.md`
- Project doctor: `docs/14_PROJECT_DOCTOR.md`
- Worktrees and commit sequencing (maintainers): `docs/20_WORKTREES_COMMIT_SEQUENCING.md`
- Case bundles (maintainers): `docs/21_CASE_BUNDLES.md`
- Release (maintainers): `docs/90_RELEASE.md`

## Kernel vs ecosystem

TaskX (kernel) validates packets, plans deterministically, executes one path (or emits a manual handoff), and writes canonical artifacts.

Everything else (scheduling, orchestration, memory, UX) belongs in the ecosystem above the kernel.

>>>>>>> codex/TP-DOCS-STRUCTURE-0002-doc-spine
