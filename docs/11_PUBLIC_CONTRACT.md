# Public Contract

This document defines dopeTask's public, user-visible contract: inputs, outputs, determinism, exit codes, and non-goals.

## Inputs

- Task Packet: see `13_TASK_PACKET_FORMAT.md`
- Route availability config: `.dopetask/runtime/availability.yaml`

## Outputs

dopeTask writes deterministic artifacts for a given invocation:

- Route plan artifacts under `out/dopetask_route/`
- Refusal reasons when refusing

Console output is informational. Artifacts are the record.

## Determinism rules

For identical:

- Packet
- Declared inputs
- dopeTask version

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

dopeTask follows Semantic Versioning.

- Patch: bug fixes only
- Minor: additive and backward-compatible
- Major: contract-breaking

