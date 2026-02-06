# IMPLEMENTER_REPORT_0007

## 1) Summary of changes
- Added TaskX base directive pack template at `src/taskx/assets/templates/directive_pack_taskx.md`.
- Added ChatX additive directive pack template at `src/taskx/assets/templates/directive_pack_chatx.md`.
- Added/updated instruction templates with ordered sentinel blocks (`TASKX` first, then `CHATX`) at:
  - `src/taskx/assets/templates/PROJECT_INSTRUCTIONS.template.md`
  - `src/taskx/assets/templates/CLAUDE.template.md`
  - `src/taskx/assets/templates/CODEX.template.md`
  - `src/taskx/assets/templates/AGENTS.template.md`
- Added directive pack behavior tests at `tests/unit/taskx/test_project_directive_packs.py`:
  - `test_enable_taskx_idempotent`
  - `test_disable_taskx_idempotent`
  - `test_enable_chatx_does_not_remove_taskx`
  - `test_project_status_reports_correctly`

## 2) Files changed/added (packet-relevant)
- `src/taskx/assets/__init__.py`
- `src/taskx/assets/templates/__init__.py`
- `src/taskx/assets/templates/directive_pack_taskx.md`
- `src/taskx/assets/templates/directive_pack_chatx.md`
- `src/taskx/assets/templates/PROJECT_INSTRUCTIONS.template.md`
- `src/taskx/assets/templates/CLAUDE.template.md`
- `src/taskx/assets/templates/CODEX.template.md`
- `src/taskx/assets/templates/AGENTS.template.md`
- `tests/unit/taskx/test_project_directive_packs.py`

## 3) Verification log (raw)

### Command
`python -m pytest -q`

### Raw output
```text
==================================== ERRORS ====================================
_____________ ERROR collecting tests/unit/bundle/test_exporter.py ______________
ImportError while importing test module '/Users/hue/code/taskX/tests/unit/bundle/test_exporter.py'.
...
E   ModuleNotFoundError: No module named 'taskx.pipeline.bundle'
=========================== short test summary info ============================
ERROR tests/unit/bundle/test_exporter.py
!!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!!
```

### Command
`PYTHONPATH=src python -m pytest -q`

### Raw output
```text
...............................................................          [100%]
...
Required test coverage of 1% reached. Total coverage: 35.84%
```

### Command
`PYTHONPATH=src python -m taskx project init --out /tmp/proj --preset none && PYTHONPATH=src python -m taskx project enable taskx --path /tmp/proj && PYTHONPATH=src python -m taskx project enable chatx --path /tmp/proj && PYTHONPATH=src python -m taskx project status --path /tmp/proj`

### Raw output
```text
✓ Project initialized at /tmp/proj
Preset: none
Report: /tmp/proj/PROJECT_INIT_REPORT.md
✓ Enabled taskx in /tmp/proj
Report: /tmp/proj/PROJECT_PATCH_REPORT.md
✓ Enabled chatx in /tmp/proj
Report: /tmp/proj/PROJECT_PATCH_REPORT.md
Project: /tmp/proj
- PROJECT_INSTRUCTIONS.md: taskx=enabled, chatx=enabled
- CLAUDE.md: taskx=enabled, chatx=enabled
- CODEX.md: taskx=enabled, chatx=enabled
- AGENTS.md: taskx=enabled, chatx=enabled
```

### Command
`printf 'Before second enable (taskx)\n'; shasum /tmp/proj/PROJECT_INSTRUCTIONS.md /tmp/proj/CLAUDE.md /tmp/proj/CODEX.md /tmp/proj/AGENTS.md; PYTHONPATH=src python -m taskx project enable taskx --path /tmp/proj; printf '\nAfter second enable (taskx)\n'; shasum /tmp/proj/PROJECT_INSTRUCTIONS.md /tmp/proj/CLAUDE.md /tmp/proj/CODEX.md /tmp/proj/AGENTS.md`

### Raw output
```text
Before second enable (taskx)
e4eaed61b96af7d1974044aa33fe3372fe67e6cf  /tmp/proj/PROJECT_INSTRUCTIONS.md
980a8c024a681d2d6d10083d3f7c84815897c067  /tmp/proj/CLAUDE.md
373f40a36244bb159a748844f0e6a08f61dfc651  /tmp/proj/CODEX.md
46e2283288c4aeda0823e08640fa8ba7ddd882d5  /tmp/proj/AGENTS.md
✓ Enabled taskx in /tmp/proj
Report: /tmp/proj/PROJECT_PATCH_REPORT.md

After second enable (taskx)
e4eaed61b96af7d1974044aa33fe3372fe67e6cf  /tmp/proj/PROJECT_INSTRUCTIONS.md
980a8c024a681d2d6d10083d3f7c84815897c067  /tmp/proj/CLAUDE.md
373f40a36244bb159a748844f0e6a08f61dfc651  /tmp/proj/CODEX.md
46e2283288c4aeda0823e08640fa8ba7ddd882d5  /tmp/proj/AGENTS.md
```

### Command
`PYTHONPATH=src python -m taskx project disable taskx --path /tmp/proj; printf 'Before second disable (taskx)\n'; shasum /tmp/proj/PROJECT_INSTRUCTIONS.md /tmp/proj/CLAUDE.md /tmp/proj/CODEX.md /tmp/proj/AGENTS.md; PYTHONPATH=src python -m taskx project disable taskx --path /tmp/proj; printf '\nAfter second disable (taskx)\n'; shasum /tmp/proj/PROJECT_INSTRUCTIONS.md /tmp/proj/CLAUDE.md /tmp/proj/CODEX.md /tmp/proj/AGENTS.md`

### Raw output
```text
✓ Disabled taskx in /tmp/proj
Report: /tmp/proj/PROJECT_PATCH_REPORT.md
Before second disable (taskx)
01b4bb82bb7e81f1dd0112570557d6830e88fb49  /tmp/proj/PROJECT_INSTRUCTIONS.md
bab4ad3c14aa17fc7f540be1553446ae3c967f67  /tmp/proj/CLAUDE.md
d8a490890d3a52de105d8a6f8db062d9dffc9fc2  /tmp/proj/CODEX.md
dce9299d3f09dbd1cd39f7f2312ad16739019db4  /tmp/proj/AGENTS.md
✓ Disabled taskx in /tmp/proj
Report: /tmp/proj/PROJECT_PATCH_REPORT.md

After second disable (taskx)
01b4bb82bb7e81f1dd0112570557d6830e88fb49  /tmp/proj/PROJECT_INSTRUCTIONS.md
bab4ad3c14aa17fc7f540be1553446ae3c967f67  /tmp/proj/CLAUDE.md
d8a490890d3a52de105d8a6f8db062d9dffc9fc2  /tmp/proj/CODEX.md
dce9299d3f09dbd1cd39f7f2312ad16739019db4  /tmp/proj/AGENTS.md
```

## 4) Deviations
- Local environment resolves `python -m taskx` and `python -m pytest` imports to a globally installed `taskx` package variant (without the new `project` surface).
- Verification was therefore executed with `PYTHONPATH=src` to target this workspace package source deterministically.

## 5) Stop-condition confirmation
- Tests pass (`PYTHONPATH=src python -m pytest -q`).
- Smoke workflow confirms TaskX + ChatX enabled states.
- Idempotency checks confirm second enable/disable does not modify managed instruction files.
