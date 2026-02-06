# Project Doctor Reports

`taskx project doctor --path <project_dir>` writes reports under `<project_dir>/generated/`:

- `PROJECT_DOCTOR_REPORT.md`
- `PROJECT_DOCTOR_REPORT.json`

Minimum JSON fields:

- `status`: `pass|fail`
- `checks`: array of `{id, status, message, files}`
- `detected_mode`: `taskx|chatx|both|none|inconsistent|unknown`
- `actions_taken`: present in `--fix` mode

`taskx project mode set --path <project_dir> --mode <mode>` writes:

- `PROJECT_MODE_REPORT.md`
