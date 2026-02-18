# Security Policy

TaskX is deterministic and artifact-first. If you find a way to bypass validation, alter artifacts, or compromise deterministic behavior, report it privately.

## Supported Versions

Only the latest minor version is supported.

## Reporting a Vulnerability

Please do not open public issues for security reports.

Send a private report including:
- version
- operating system and Python version
- reproduction steps
- redacted packet
- relevant artifact output (redacted)

We target an initial response within 72 hours.

## What Counts as Security-Relevant

- validation bypass
- artifact tampering or suppression
- exit code manipulation
- hidden network calls
- determinism compromise
- unauthorized runner substitution
