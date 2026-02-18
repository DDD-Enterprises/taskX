# Contract Audit Schema and Rubric

This document defines deterministic classification rules for contract-to-code audits of absolute claims (for example: "will never", "guarantees", "no hidden").

## Statuses

- `PROVEN`: direct enforcement in code and/or tests; clear guardrails; no known bypass path in normal operation.
- `PARTIAL`: intent present but incomplete enforcement; relies on convention; or only enforced in some modes.
- `UNKNOWN`: no evidence found; ambiguous; or only implied by docs.
- `CONFLICT`: code behavior contradicts docs.

## Evidence Rules

Each classification must include at least one evidence item:

- file path + line range,
- exact `rg`/grep hit + snippet, or
- test name that asserts the invariant.

Evidence must be traceable and reproducible from the repository state being audited.

## Claim Record Format

Every claim entry in the report must use this field set:

- `claim_id`
- `doc_source`
- `claim_text`
- `status`
- `evidence`
- `notes`
- `risk`
- `next_action`

## Classification Procedure

1. Start from a verbatim claim extracted from docs.
2. Locate implementation and tests that enforce or contradict the claim.
3. Assign exactly one status (`PROVEN`, `PARTIAL`, `UNKNOWN`, `CONFLICT`).
4. Attach evidence meeting the rules above.
5. Record residual risk and the smallest deterministic next action.
