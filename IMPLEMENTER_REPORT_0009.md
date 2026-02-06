# IMPLEMENTER_REPORT_0009

## Summary

Implemented Task Packet 0009:

- Added master mode toggle command: `taskx project mode set --path <dir> --mode {taskx|chatx|both|none}`
- Added project doctor command: `taskx project doctor --path <dir> [--fix] [--mode ...]`
- Added new modules:
  - `/Users/hue/code/taskX/src/taskx/project/mode.py`
  - `/Users/hue/code/taskX/src/taskx/project/doctor.py`
- Added CLI wiring in `/Users/hue/code/taskX/src/taskx/cli.py`
- Added tests:
  - `/Users/hue/code/taskX/tests/unit/taskx/test_project_mode_doctor.py`
- Added minimal report format docs:
  - `/Users/hue/code/taskX/docs/PROJECT_DOCTOR.md`

## Created/updated generated artifacts behavior

- Mode command writes:
  - `<project_dir>/generated/PROJECT_MODE_REPORT.md`
- Doctor command writes:
  - `<project_dir>/generated/PROJECT_DOCTOR_REPORT.md`
  - `<project_dir>/generated/PROJECT_DOCTOR_REPORT.json`
- Fix mode generates:
  - `<project_dir>/generated/SUPERVISOR_PRIMING_PROMPT.txt`

## Environment note

This shell resolved `python -m taskx` to another local checkout by default. Verification commands were executed with `PYTHONPATH=src` to target `/Users/hue/code/taskX`.

## Raw verification logs

### 1) `python -m pytest -q`

Command:

```bash
python -m pytest -q
```

Raw output:

```text
pyenv: cannot rehash: /Users/hue/.pyenv/shims isn't writable
....................................................................     [100%]
================================ tests coverage ================================
_______________ coverage: platform darwin, python 3.13.6-final-0 _______________

Name                                           Stmts   Miss Branch BrPart  Cover   Missing
------------------------------------------------------------------------------------------
src/taskx/__init__.py                              1      0      0      0   100%
src/taskx/assets/__init__.py                       0      0      0      0   100%
src/taskx/assets/templates/__init__.py             0      0      0      0   100%
src/taskx/ci_gate.py                             168    168     54      0     0%   8-406
src/taskx/cli.py                                 576    437     76      1    22%   17-18, 22-23, 27-28, 32-33, 37-38, 42-43, 49-51, 55-56, 60-61, 65-66, 90-100, 105-107, 138-168, 199-233, 264-279, 315-347, 379-403, 449-481, 516-535, 586-623, 645-646, 654-657, 688-726, 757-790, 825-849, 884-918, 949-979, 1006-1040, 1091-1130, 1172-1206, 1269-1318, 1380-1385, 1406-1411, 1431-1436, 1458-1459, 1479-1495, 1517-1541, 1554-1556, 1560-1562, 1573-1585, 1599-1610, 1624-1626, 1644-1655
src/taskx/doctor.py                              191     32     42     18    77%   66, 81-82, 110, 133-134, 157, 170, 184-196, 214-215, 219->225, 220->219, 233, 249->252, 255, 272, 306, 330-331, 352-353, 375-376, 379->385, 380->379, 397->400, 467, 479-485, 492
src/taskx/git/__init__.py                          2      0      0      0   100%
src/taskx/git/commit_run.py                      124     23     28      3    83%   16, 119-121, 148-149, 174-176, 184-186, 192, 199, 209, 227-229, 248-250, 257-259
src/taskx/pipeline/__init__.py                     0      0      0      0   100%
src/taskx/pipeline/bundle/__init__.py              0      0      0      0   100%
src/taskx/pipeline/bundle/exporter.py            170     35     62     14    75%   34-41, 54->61, 62->74, 65-72, 90-98, 126->125, 138-139, 140->131, 156-157, 192, 194, 199-201, 209, 255-256
src/taskx/pipeline/bundle/ingester.py            186     37     74     22    75%   37, 41, 45-46, 106-108, 131, 142, 155-162, 172-179, 186-193, 198-206, 208->218, 218->170, 230, 254-264, 312, 315, 328, 331, 334, 344, 355, 360
src/taskx/pipeline/case/__init__.py                0      0      0      0   100%
src/taskx/pipeline/case/auditor.py               261    104    118     25    52%   34-36, 59, 68, 73-84, 95, 99, 103, 129-156, 197-200, 232-244, 253-257, 276-296, 329-359, 395->398, 399, 417-418, 444, 460->477, 482, 500, 515, 527->544, 545, 588, 591, 601-605
src/taskx/pipeline/compliance/__init__.py          2      0      0      0   100%
src/taskx/pipeline/compliance/gate.py            161    140     80      0     9%   43-123, 128-137, 142-145, 150-176, 187-216, 230-243, 249-263, 268-296, 302-305, 315-354, 367-416
src/taskx/pipeline/compliance/types.py            17      0      0      0   100%
src/taskx/pipeline/evidence/__init__.py            2      0      0      0   100%
src/taskx/pipeline/evidence/collector.py         171    154     74      0     7%   39-147, 156-166, 175-195, 212-283, 289-315, 325-349, 355-360, 365-373, 392-452
src/taskx/pipeline/evidence/types.py              15      0      0      0   100%
src/taskx/pipeline/loop/__init__.py                3      0      0      0   100%
src/taskx/pipeline/loop/orchestrator.py          226    195     94      0    10%   45-103, 114-156, 177-236, 261-324, 345-403, 425-494, 509, 524-527, 532-545, 550-558, 569-586, 616-652
src/taskx/pipeline/loop/types.py                  23      0      0      0   100%
src/taskx/pipeline/promotion/__init__.py           2      0      0      0   100%
src/taskx/pipeline/promotion/gate.py             125    112     54      0     7%   37-167, 172-200, 206-232, 241-269, 282-318
src/taskx/pipeline/promotion/types.py             16      0      0      0   100%
src/taskx/pipeline/spec_feedback/__init__.py       3      0      0      0   100%
src/taskx/pipeline/spec_feedback/feedback.py     172    155     70      0     7%   34-82, 89-108, 115-225, 230-319, 324, 339-346, 356-400, 410-448
src/taskx/pipeline/spec_feedback/types.py         13      0      0      0   100%
src/taskx/pipeline/task_compiler/__init__.py       3      0      0      0   100%
src/taskx/pipeline/task_compiler/compiler.py     176    159     88      1     7%   14, 20-28, 35-36, 45-90, 99-133, 145-168, 184-263, 286-301, 311-374, 404-513
src/taskx/pipeline/task_compiler/types.py         28      0      0      0   100%
src/taskx/pipeline/task_runner/__init__.py         3      0      0      0   100%
src/taskx/pipeline/task_runner/parser.py          90     78     46      1    10%   12, 37-84, 102-124, 132-154, 162-188, 193-210
src/taskx/pipeline/task_runner/runner.py          58     45     14      1    19%   13-15, 44-132, 146-206, 211-245, 250-301, 306-369, 374-384
src/taskx/pipeline/task_runner/types.py           16      0      0      0   100%
src/taskx/project/__init__.py                      0      0      0      0   100%
src/taskx/project/common.py                       89      8     28      7    87%   61-62, 68, 83, 98->100, 120, 129, 137, 157
src/taskx/project/doctor.py                      225     69     86     15    67%   130, 133-134, 164-173, 178-186, 204->206, 206->208, 212-214, 219-221, 235, 242, 269, 287, 297, 336-338, 356-372, 375, 381-383, 387-424
src/taskx/project/init.py                         60      5     22      5    88%   27, 49->52, 88, 107-108, 153
src/taskx/project/mode.py                         58      5     18      3    89%   25-26, 79, 90-91
src/taskx/project/toggles.py                      63      4     18      4    90%   34, 74-81, 130, 156->158
src/taskx/schemas/__init__.py                      1      0      0      0   100%
src/taskx/schemas/validator.py                    21      7      6      2    59%   9-10, 36, 50-63
src/taskx/utils/__init__.py                        0      0      0      0   100%
src/taskx/utils/json_output.py                    85     68     16      0    17%   33-75, 91-124, 137-149, 176-201, 227-252, 268-279
src/taskx/utils/package_data.py                   10     10      0      0     0%   11-73
src/taskx/utils/repo.py                          167    116     86      0    24%   62-119, 129-141, 238-276, 288-304, 319-366, 374-382, 402-443
src/taskx/utils/repo_config.py                    58     33     12      0    36%   48-79, 102-136
src/taskx/utils/schema_registry.py                64     12     14      3    81%   14-15, 61-64, 76, 108, 128-131, 157-158, 192
------------------------------------------------------------------------------------------
TOTAL                                           3905   2211   1280    125    39%
Coverage HTML written to dir htmlcov
Required test coverage of 1% reached. Total coverage: 38.78%
```

### 2) Clean project + doctor

Command:

```bash
PYTHONPATH=src python -m taskx project init --out /tmp/proj --preset none
```

Raw output:

```text
pyenv: cannot rehash: /Users/hue/.pyenv/shims isn't writable
✓ Project initialized at /tmp/proj
Preset: none
Report: /tmp/proj/PROJECT_INIT_REPORT.md
```

Command:

```bash
PYTHONPATH=src python -m taskx project doctor --path /tmp/proj
```

Raw output:

```text
pyenv: cannot rehash: /Users/hue/.pyenv/shims isn't writable
PROJECT DOCTOR
status=fail detected_mode=none

checks:
- [PASS] files_present: All required project instruction files are present
- [PASS] sentinel_integrity: TaskX/ChatX sentinel blocks are present and 
well-formed
- [PASS] pack_status_consistency: Pack status is consistent (mode=none)
- [FAIL] supervisor_prompt: generated/SUPERVISOR_PRIMING_PROMPT.txt is missing
Reports: /tmp/proj/generated/PROJECT_DOCTOR_REPORT.md, 
/tmp/proj/generated/PROJECT_DOCTOR_REPORT.json
```

### 3) Fix mode + set mode + idempotency

Command:

```bash
PYTHONPATH=src python -m taskx project mode set --path /tmp/proj --mode both
```

Raw output:

```text
pyenv: cannot rehash: /Users/hue/.pyenv/shims isn't writable
✓ Applied mode 'both' for /tmp/proj
- AGENTS.md: taskx=enabled, chatx=enabled
- CLAUDE.md: taskx=enabled, chatx=enabled
- CODEX.md: taskx=enabled, chatx=enabled
- PROJECT_INSTRUCTIONS.md: taskx=enabled, chatx=enabled
Files changed: 4
Report: /tmp/proj/generated/PROJECT_MODE_REPORT.md
```

Command:

```bash
PYTHONPATH=src python -m taskx project doctor --path /tmp/proj --fix --mode both
```

Raw output:

```text
pyenv: cannot rehash: /Users/hue/.pyenv/shims isn't writable
PROJECT DOCTOR
status=pass detected_mode=both

checks:
- [PASS] files_present: All required project instruction files are present
- [PASS] sentinel_integrity: TaskX/ChatX sentinel blocks are present and 
well-formed
- [PASS] pack_status_consistency: Pack status is consistent (mode=both)
- [PASS] supervisor_prompt: Supervisor prompt matches mode 'both'
Reports: /tmp/proj/generated/PROJECT_DOCTOR_REPORT.md, 
/tmp/proj/generated/PROJECT_DOCTOR_REPORT.json
```

Idempotency command:

```bash
find /tmp/proj -type f | sort | xargs shasum > /tmp/proj_before.sha && \
PYTHONPATH=src python -m taskx project doctor --path /tmp/proj --fix --mode both && \
find /tmp/proj -type f | sort | xargs shasum > /tmp/proj_after.sha && \
diff -u /tmp/proj_before.sha /tmp/proj_after.sha
```

Raw output:

```text
pyenv: cannot rehash: /Users/hue/.pyenv/shims isn't writable
PROJECT DOCTOR
status=pass detected_mode=both

checks:
- [PASS] files_present: All required project instruction files are present
- [PASS] sentinel_integrity: TaskX/ChatX sentinel blocks are present and 
well-formed
- [PASS] pack_status_consistency: Pack status is consistent (mode=both)
- [PASS] supervisor_prompt: Supervisor prompt matches mode 'both'
Reports: /tmp/proj/generated/PROJECT_DOCTOR_REPORT.md, 
/tmp/proj/generated/PROJECT_DOCTOR_REPORT.json
```

(`diff -u` produced no output, confirming no file changes on second run.)

### 4) Mode consistency drift check

Command:

```bash
perl -0777 -i -pe 's/<!-- CHATX:BEGIN -->\n.*?\n<!-- CHATX:END -->/<!-- CHATX:BEGIN -->\n(disabled)\n<!-- CHATX:END -->/s' /tmp/proj/AGENTS.md && \
PYTHONPATH=src python -m taskx project doctor --path /tmp/proj
```

Raw output:

```text
pyenv: cannot rehash: /Users/hue/.pyenv/shims isn't writable
PROJECT DOCTOR
status=fail detected_mode=inconsistent

checks:
- [PASS] files_present: All required project instruction files are present
- [PASS] sentinel_integrity: TaskX/ChatX sentinel blocks are present and 
well-formed
- [FAIL] pack_status_consistency: Pack status differs between files
- [FAIL] supervisor_prompt: Cannot validate supervisor prompt while mode is 
unknown/inconsistent
Reports: /tmp/proj/generated/PROJECT_DOCTOR_REPORT.md, 
/tmp/proj/generated/PROJECT_DOCTOR_REPORT.json
```

Report drift pinpoint check:

```bash
rg -n "pack_status_consistency|AGENTS.md|files" /tmp/proj/generated/PROJECT_DOCTOR_REPORT.md /tmp/proj/generated/PROJECT_DOCTOR_REPORT.json
```

Raw output:

```text
pyenv: cannot rehash: /Users/hue/.pyenv/shims isn't writable
/tmp/proj/generated/PROJECT_DOCTOR_REPORT.md:9:- id: files_present
/tmp/proj/generated/PROJECT_DOCTOR_REPORT.md:11:  - message: All required project instruction files are present
/tmp/proj/generated/PROJECT_DOCTOR_REPORT.md:12:  - files: (none)
/tmp/proj/generated/PROJECT_DOCTOR_REPORT.md:16:  - files: AGENTS.md, CLAUDE.md, CODEX.md, PROJECT_INSTRUCTIONS.md
/tmp/proj/generated/PROJECT_DOCTOR_REPORT.md:17:- id: pack_status_consistency
/tmp/proj/generated/PROJECT_DOCTOR_REPORT.md:19:  - message: Pack status differs between files
/tmp/proj/generated/PROJECT_DOCTOR_REPORT.md:20:  - files: AGENTS.md
/tmp/proj/generated/PROJECT_DOCTOR_REPORT.md:24:  - files: /tmp/proj/generated/SUPERVISOR_PRIMING_PROMPT.txt
/tmp/proj/generated/PROJECT_DOCTOR_REPORT.md:28:- AGENTS.md: taskx=enabled chatx=disabled
/tmp/proj/generated/PROJECT_DOCTOR_REPORT.json:4:      "files": [],
/tmp/proj/generated/PROJECT_DOCTOR_REPORT.json:5:      "id": "files_present",
/tmp/proj/generated/PROJECT_DOCTOR_REPORT.json:6:      "message": "All required project instruction files are present",
/tmp/proj/generated/PROJECT_DOCTOR_REPORT.json:10:      "files": [
/tmp/proj/generated/PROJECT_DOCTOR_REPORT.json:11:        "AGENTS.md",
/tmp/proj/generated/PROJECT_DOCTOR_REPORT.json:21:      "files": [
/tmp/proj/generated/PROJECT_DOCTOR_REPORT.json:22:        "AGENTS.md"
/tmp/proj/generated/PROJECT_DOCTOR_REPORT.json:24:      "id": "pack_status_consistency",
/tmp/proj/generated/PROJECT_DOCTOR_REPORT.json:25:      "message": "Pack status differs between files",
/tmp/proj/generated/PROJECT_DOCTOR_REPORT.json:29:      "files": [
/tmp/proj/generated/PROJECT_DOCTOR_REPORT.json:39:    "AGENTS.md": {
```
