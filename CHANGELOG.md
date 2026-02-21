# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project follows Semantic Versioning.

## [Unreleased]

### Added

- Governance and contribution documentation.

### Changed

- N/A

### Fixed

- N/A

## [0.1.3] - 2026-02-21

### Added

- No user-facing features; release focused on public-release hardening.

### Changed

- Renamed the PyPI distribution to `taskx-kernel` to avoid `taskx` namespace conflict.
- Unified package metadata and runtime versioning to `0.1.3`.
- Hardened tag-driven release workflow with frozen dependency sync and pre-publish lint/type/test gates.

### Fixed

- Resolved `ruff` and `mypy` gate failures in CLI/ops/guard code paths.
- Removed duplicate `wt start`, `commit-sequence`, and `finish` command definitions from CLI registration.
- Removed broken legacy/placeholder workflows that were not operable in this repository state.

## [0.1.0] - 2026-02-18

### Added

- Initial public release baseline.
