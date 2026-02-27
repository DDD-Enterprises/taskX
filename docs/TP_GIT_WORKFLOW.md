# TP Git Workflow

dopeTask now provides a fail-closed Task Packet git surface under `dopetask tp git`.

## Required flow

1. `dopetask tp git doctor`
2. `dopetask tp git start <TP_ID> <slug>`
3. Do implementation work in `.worktrees/<TP_ID>`
4. `dopetask tp git pr <TP_ID> --title "..." [--body ... | --body-file ...]`
5. `dopetask tp git merge <TP_ID>`
6. `dopetask tp git sync-main`
7. `dopetask tp git cleanup <TP_ID>`

## Command reference

- `dopetask tp git doctor [--repo <path>]`
- `dopetask tp git start <TP_ID> <slug> [--repo <path>] [--reuse]`
- `dopetask tp git status <TP_ID> [--repo <path>]`
- `dopetask tp git pr <TP_ID> --title "..." [--body ... | --body-file ...] [--repo <path>]`
- `dopetask tp git merge <TP_ID> [--squash|--merge|--rebase] [--repo <path>]`
- `dopetask tp git sync-main [--repo <path>]`
- `dopetask tp git cleanup <TP_ID> [--repo <path>]`
- `dopetask tp git list [--repo <path>]`

## Fail-closed rules

- Doctor refuses when branch is not `main`.
- Doctor refuses when `git status --porcelain` is non-empty.
- Doctor refuses when `git stash list` is non-empty.
- Merge refuses when `gh` auth is missing or auto-merge cannot be enabled.
- Cleanup refuses dirty worktrees.
