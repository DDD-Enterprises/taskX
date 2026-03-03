# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project follows Semantic Versioning.

## [Unreleased]

### Added

- Governance and contribution documentation.
- Python 3.9 compatibility coverage for TOML parsing and adapter entry-point discovery.

### Changed

- Lowered the supported Python floor from 3.11 to 3.9.
- Updated packaging metadata, lint/type targets, and lock resolution to support Python 3.9+ environments.

### Fixed

- Removed Python 3.10+/3.11-only syntax and stdlib assumptions that blocked installation or runtime use on Python 3.9.

## [0.1.3] - 2026-02-21

### Added

- No user-facing features; release focused on public-release hardening.

### Changed

- Renamed the PyPI distribution to `dopetask` (previously `dopetask-kernel`).
- Unified package metadata and runtime versioning to `0.1.3`.
- Hardened tag-driven release workflow with frozen dependency sync and pre-publish lint/type/test gates.

### Fixed

- Resolved `ruff` and `mypy` gate failures in CLI/ops/guard code paths.
- Removed duplicate `wt start`, `commit-sequence`, and `finish` command definitions from CLI registration.
- Removed broken legacy/placeholder workflows that were not operable in this repository state.

## [0.1.0] - 2026-02-21

### Added

- Initial public release baseline.
- Deterministic build hash verification and wheel smoke validation in CI.
- Tag-gated release and container distribution workflows.

### Changed

- Release flow is CI-driven from version tags with uv-native build/publish steps.

### Fixed

- Removed legacy manual release workflow to enforce a single release path.
