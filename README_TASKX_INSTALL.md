# TaskX Installation Guide

TaskX is a minimal task packet lifecycle system designed for deterministic, offline-first development workflows. This guide covers installation, upgrading, and release management.

## Quick Start

### Option 1: Install from Git Tag (Simplest)

No wheel download needed, works from any machine with git and pip:

```bash
pip install "taskx @ git+ssh://git@github.com/OWNER/REPO.git@v0.1.0"
```

Replace:
- `OWNER/REPO` with your repository path (e.g., `myorg/ChatRipperXXX`)
- `v0.1.0` with the desired version tag

**Pros:**
- No manual wheel download
- Works in CI/CD without extra steps
- Always installs from tagged, immutable code

**Cons:**
- Requires git and SSH access to GitHub
- Slower than wheel installs (must build from source)

### Option 2: Install from Release Wheel (Fastest)

Download the wheel from [GitHub Releases](https://github.com/OWNER/REPO/releases):

1. Navigate to the desired release (e.g., `v0.1.0`)
2. Download `taskx-0.1.0-py3-none-any.whl` from assets
3. Install:

```bash
pip install ./taskx-0.1.0-py3-none-any.whl
```

**Pros:**
- Fastest installation (no build required)
- No git or build toolchain needed
- Works in air-gapped environments

**Cons:**
- Manual download step
- Must manage wheel file location

## Installation in Projects

### In a New Project

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install TaskX
pip install "taskx @ git+ssh://git@github.com/OWNER/REPO.git@v0.1.0"

# Verify installation
taskx --version
taskx doctor
```

### In requirements.txt

```
# requirements.txt
taskx @ git+ssh://git@github.com/OWNER/REPO.git@v0.1.0
```

Then:
```bash
pip install -r requirements.txt
```

### In pyproject.toml (Poetry/Hatch)

```toml
[project.dependencies]
# For Hatch/setuptools
taskx = { git = "ssh://git@github.com/OWNER/REPO.git", tag = "v0.1.0" }

# Or for Poetry:
[tool.poetry.dependencies]
taskx = { git = "ssh://git@github.com/OWNER/REPO.git", tag = "v0.1.0" }
```

## Upgrading TaskX

### Upgrade to Latest Release

```bash
# From git tag
pip install --upgrade "taskx @ git+ssh://git@github.com/OWNER/REPO.git@v0.2.0"

# From wheel (download new version first)
pip install --upgrade ./taskx-0.2.0-py3-none-any.whl
```

### Check Current Version

```bash
python -c "import taskx; print(taskx.__version__)"
# Or
taskx --version
```

### Verify Installation Health

After installing or upgrading, always run:

```bash
taskx doctor
```

This checks:
- ✅ TaskX imports correctly
- ✅ Schema files are bundled and accessible
- ✅ All required schemas present
- ✅ Package installation is healthy

## For Maintainers: Cutting a Release

### 1. Prepare Release

1. **Update version** in two places:
   - `src/taskx/__init__.py`: Set `__version__ = "0.2.0"`
   - `pyproject.toml`: Set `version = "0.2.0"`

2. **Commit version bump:**
   ```bash
   git add src/taskx/__init__.py pyproject.toml
   git commit -m "chore: bump version to 0.2.0"
   ```

3. **Run tests locally:**
   ```bash
   python -m pytest -q
   bash scripts/taskx_build.sh
   bash scripts/taskx_install_test.sh
   ```

### 2. Create and Push Tag

```bash
git tag v0.2.0
git push origin v0.2.0
```

**Important:** Tag must be in format `vX.Y.Z` (semantic versioning with leading `v`).

### 3. Automated Release Process

Once the tag is pushed, GitHub Actions automatically:

1. ✅ Validates version consistency (tag vs `__version__` vs pyproject.toml)
2. ✅ Runs full test suite
3. ✅ Builds sdist + wheel
4. ✅ Tests wheel installation in clean venv
5. ✅ Runs `taskx doctor` to verify schema bundling
6. ✅ Creates GitHub Release with:
   - Release notes
   - Wheel asset
   - Source distribution asset

### 4. Release Verification

After release is published:

1. **Check release page:**
   https://github.com/OWNER/REPO/releases/tag/vX.Y.Z

2. **Test installation from tag:**
   ```bash
   python -m venv /tmp/test-taskx
   source /tmp/test-taskx/bin/activate
   pip install "taskx @ git+ssh://git@github.com/OWNER/REPO.git@v0.2.0"
   taskx doctor
   deactivate
   rm -rf /tmp/test-taskx
   ```

3. **Test installation from wheel:**
   Download the wheel asset and:
   ```bash
   python -m venv /tmp/test-taskx-wheel
   source /tmp/test-taskx-wheel/bin/activate
   pip install ./taskx-0.2.0-py3-none-any.whl
   taskx doctor
   deactivate
   rm -rf /tmp/test-taskx-wheel
   ```

## Troubleshooting

### Schema Bundling Issues

If `taskx doctor` reports missing schemas after installation:

```
❌ Error: Missing required schemas: allowlist_diff, promotion_token, ...
```

**Cause:** Schemas weren't bundled in the wheel.

**Fix:**
1. Verify `taskx_schemas/__init__.py` exists
2. Check `pyproject.toml` includes:
   ```toml
   [tool.hatch.build.targets.wheel]
   packages = ["src/taskx", "taskx_schemas"]
   ```
3. Rebuild and reinstall:
   ```bash
   bash scripts/taskx_build.sh
   bash scripts/taskx_install_test.sh
   ```

### Git SSH Authentication

If git tag installation fails with authentication errors:

**Option 1:** Ensure SSH keys are configured:
```bash
ssh -T git@github.com
```

**Option 2:** Use HTTPS (requires GitHub token):
```bash
pip install "taskx @ git+https://github.com/OWNER/REPO.git@v0.1.0"
```

### Version Mismatch Errors

If release workflow fails with version mismatch:

```
❌ Error: Tag version (0.2.0) does not match pyproject.toml (0.1.0)
```

**Fix:**
1. Delete the tag: `git tag -d v0.2.0 && git push origin :refs/tags/v0.2.0`
2. Update both version files to match
3. Create new tag

## CI/CD Integration

### GitHub Actions Example

```yaml
name: My Project CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      
      - name: Install TaskX
        run: |
          pip install "taskx @ git+ssh://git@github.com/OWNER/REPO.git@v0.1.0"
      
      - name: Verify TaskX Installation
        run: |
          taskx doctor
      
      - name: Use TaskX Commands
        run: |
          taskx compile-tasks --mode mvp
          taskx run-task --task-id T001
```

### Pre-commit Hook Example

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Ensure TaskX is installed
if ! command -v taskx &> /dev/null; then
    echo "TaskX not found. Installing..."
    pip install "taskx @ git+ssh://git@github.com/OWNER/REPO.git@v0.1.0"
fi

# Run CI gate before allowing commit
taskx ci-gate --require-promotion=false
```

## Version Pinning Recommendations

### For Production

Pin to exact versions in production:

```bash
# requirements.txt
taskx @ git+ssh://git@github.com/OWNER/REPO.git@v0.1.0
```

### For Development

Use latest patch version:

```bash
# requirements-dev.txt
taskx @ git+ssh://git@github.com/OWNER/REPO.git@v0.1
```

Or latest version (not recommended):

```bash
taskx @ git+ssh://git@github.com/OWNER/REPO.git@main
```

## Unified Installer Script

For projects that need TaskX, use the unified installer script instead of manual pip commands. This provides consistent installation and automatic verification across all your projects.

The installer supports **version pinning via lockfile** (`TASKX_VERSION.lock`) so you never have to export environment variables or remember version numbers across projects.

### Quick Usage

#### With Lockfile (Recommended)

Create `TASKX_VERSION.lock` in your repo root:

```
# TaskX install pin for this repo
version = 0.3.0
mode = git
owner = myorg
repo = taskx
```

Then simply run:

```bash
bash scripts/install_taskx.sh
```

The installer reads the lockfile and installs the pinned version automatically.

#### Without Lockfile (Environment Variables)

The installer supports three modes: **GitHub Packages** (private index), **Git** (tag/commit), and **Local** (editable).

#### Auto Mode (Recommended)

The installer auto-detects the mode based on environment variables:

```bash
# For GitHub Packages install
export TASKX_OWNER=your-github-org
export TASKX_VERSION=0.3.0
export TASKX_PKG_TOKEN=ghp_your_token_with_read_packages

bash scripts/install_taskx.sh
```

```bash
# For Git tag install
export TASKX_OWNER=your-github-org
export TASKX_REPO=your-taskx-repo
export TASKX_VERSION=0.3.0

bash scripts/install_taskx.sh
```

```bash
# For local development
export TASKX_LOCAL_PATH=/absolute/path/to/taskx/checkout

bash scripts/install_taskx.sh
```

#### Explicit Mode Selection

Override auto-detection:

```bash
bash scripts/install_taskx.sh --mode packages
bash scripts/install_taskx.sh --mode git
bash scripts/install_taskx.sh --mode local
```

#### Verify-Only Mode

Check existing installation without reinstalling:

```bash
bash scripts/install_taskx.sh --verify-only
```

This runs:
- `taskx --help` (smoke test)
- `taskx doctor --timestamp-mode deterministic` (health check)

### Lockfile Support (TASKX_VERSION.lock)

The installer can read configuration from a `TASKX_VERSION.lock` file in your repo root. This eliminates the need to set environment variables for every project.

#### Lockfile Format

```
# TaskX install pin for this repo
# Required:
version = 0.3.0

# Optional:
mode = git
owner = myorg
repo = taskx
ref = v0.3.0
git_url = git+ssh://git@github.com/myorg/taskx.git
index_url = https://pip.pkg.github.com/myorg/simple
extra_index_url = https://pypi.org/simple
```

**Rules:**
- Lines starting with `#` are comments
- Blank lines are ignored
- Format: `key = value` (whitespace around `=` is allowed)
- Values are not quoted
- Unknown keys cause hard failure (prevents typos)
- `version` must be `X.Y.Z` format (strict semver triplet)

**Allowed keys:**
- `version` - Version number (required)
- `ref` - Git ref (tag, branch, or commit)
- `mode` - Install mode: `auto`, `packages`, `git`, `local`
- `owner` - GitHub owner/organization
- `repo` - Repository name
- `git_url` - Full git URL
- `index_url` - Package index URL
- `extra_index_url` - Fallback package index URL

#### Priority Rules

Environment variables **always override** lockfile values:

1. Explicit env vars (highest priority)
2. Lockfile values
3. Defaults (lowest priority)

Example:
```bash
# Lockfile says version = 0.3.0
# But env var overrides:
export TASKX_VERSION=0.3.1
bash scripts/install_taskx.sh
# Installs 0.3.1 (from env var, not lockfile)
```

#### Lockfile Flags

**`--lockfile <path>`** - Specify lockfile location (default: `./TASKX_VERSION.lock`)

```bash
bash scripts/install_taskx.sh --lockfile /path/to/custom.lock
```

**`--write-lock`** - Write resolved config back to lockfile (never includes secrets)

```bash
# Install and save config to lockfile
export TASKX_VERSION=0.3.0
export TASKX_OWNER=myorg
export TASKX_REPO=taskx
bash scripts/install_taskx.sh --write-lock
```

**`--print-config`** - Print resolved configuration (redacts token)

```bash
bash scripts/install_taskx.sh --print-config
```

Output:
```
[INFO] Resolved Configuration:
=======================
MODE: git
TASKX_VERSION: 0.3.0
TASKX_REF: v0.3.0
TASKX_OWNER: myorg
TASKX_REPO: taskx
TASKX_GIT_URL: <not set>
TASKX_LOCAL_PATH: <not set>
TASKX_INDEX_URL: <not set>
TASKX_EXTRA_INDEX_URL: https://pypi.org/simple
TASKX_PKG_TOKEN: ***REDACTED***
TASKX_PIP: python -m pip
LOCKFILE: ./TASKX_VERSION.lock
```

#### Lockfile Workflow

**Initial setup (per project):**

```bash
# Option 1: Manual creation
cat > TASKX_VERSION.lock <<EOF
version = 0.3.0
mode = git
owner = myorg
repo = taskx
EOF

# Option 2: Install and write
export TASKX_VERSION=0.3.0
export TASKX_OWNER=myorg
export TASKX_REPO=taskx
bash scripts/install_taskx.sh --write-lock
```

**Daily usage:**

```bash
# Just run the installer - it reads the lockfile
bash scripts/install_taskx.sh
```

**Upgrading TaskX:**

```bash
# Edit lockfile
vim TASKX_VERSION.lock  # Change version = 0.3.1

# Reinstall
bash scripts/install_taskx.sh
```

**Or upgrade and write back:**

```bash
export TASKX_VERSION=0.3.1
bash scripts/install_taskx.sh --write-lock
```

#### Lockfile Examples

**For Git mode:**
```
version = 0.3.0
mode = git
owner = myorg
repo = taskx
ref = v0.3.0
```

**For GitHub Packages mode:**
```
version = 0.3.0
mode = packages
owner = myorg
# Note: TASKX_PKG_TOKEN must be set in env (never in lockfile)
```

**For local development:**
```
version = 0.3.0-dev
mode = local
# Note: TASKX_LOCAL_PATH must be set in env
```

**Minimal (auto mode):**
```
version = 0.3.0
owner = myorg
repo = taskx
# mode = auto will detect git if owner+repo present
```

### Mode Details

#### Packages Mode

Installs from GitHub Packages (private Python index).

**Required environment variables:**
- `TASKX_VERSION` - Exact version (e.g., `0.3.0`)
- `TASKX_OWNER` - GitHub owner/org
- `TASKX_PKG_TOKEN` - GitHub Personal Access Token with `read:packages` scope

**Optional:**
- `TASKX_INDEX_URL` - Override index URL (default: `https://pip.pkg.github.com/${OWNER}/simple`)
- `TASKX_EXTRA_INDEX_URL` - Fallback index (default: PyPI)

**Example:**
```bash
export TASKX_OWNER=myorg
export TASKX_VERSION=0.3.1
export TASKX_PKG_TOKEN=ghp_xxxxxxxxxxxx

bash scripts/install_taskx.sh --mode packages
```

**Security note:** Token is never printed in logs. Index URL is shown redacted as `https://***@pip.pkg.github.com/...`

#### Git Mode

Installs from a git repository using a tag, branch, or commit.

**Required:**
- Either `TASKX_REF` (e.g., `v0.3.0`, `main`, or commit SHA)
- Or `TASKX_VERSION` (e.g., `0.3.0` → constructs ref `v0.3.0`)

**And either:**
- `TASKX_GIT_URL` (full git URL)
- Or `TASKX_OWNER` + `TASKX_REPO` (constructs SSH URL)

**Examples:**
```bash
# Using owner + repo + version
export TASKX_OWNER=myorg
export TASKX_REPO=taskx
export TASKX_VERSION=0.3.0

bash scripts/install_taskx.sh --mode git
# Installs from: git+ssh://git@github.com/myorg/taskx.git@v0.3.0
```

```bash
# Using explicit git URL + ref
export TASKX_GIT_URL=git+ssh://git@github.com/myorg/taskx.git
export TASKX_REF=v0.3.0

bash scripts/install_taskx.sh --mode git
```

```bash
# HTTPS git URL (requires token in URL or git credential helper)
export TASKX_GIT_URL=git+https://github.com/myorg/taskx.git
export TASKX_REF=main

bash scripts/install_taskx.sh --mode git
```

#### Local Mode

Installs TaskX in editable mode from a local checkout.

**Required:**
- `TASKX_LOCAL_PATH` - Absolute path to TaskX repository

**Optional:**
- `TASKX_VERSION` - Document expected version (warning if not set)

**Example:**
```bash
export TASKX_LOCAL_PATH=/home/user/code/taskx

bash scripts/install_taskx.sh --mode local
```

### Auto-Detection Priority

When using `--mode auto` (or no mode flag), the installer checks:

1. **Packages mode** if `TASKX_PKG_TOKEN` is set
2. **Git mode** if `TASKX_GIT_URL` or (`TASKX_OWNER` + `TASKX_REPO`) is set
3. **Local mode** if `TASKX_LOCAL_PATH` is set
4. **Fails** if none of the above

### Environment Variables Reference

| Variable | Modes | Description |
|----------|-------|-------------|
| `TASKX_VERSION` | packages, git* | Version number (e.g., `0.3.0`) |
| `TASKX_REF` | git | Git ref: tag, branch, or commit SHA |
| `TASKX_OWNER` | packages, git* | GitHub owner/organization |
| `TASKX_REPO` | git* | Repository name |
| `TASKX_GIT_URL` | git | Full git URL (overrides owner+repo) |
| `TASKX_LOCAL_PATH` | local | Absolute path to local TaskX checkout |
| `TASKX_PKG_TOKEN` | packages | GitHub PAT with `read:packages` |
| `TASKX_INDEX_URL` | packages | Package index URL |
| `TASKX_EXTRA_INDEX_URL` | packages | Fallback index (default: PyPI) |
| `TASKX_PIP` | all | pip command (default: `python -m pip`) |

*\*For git mode: Either `TASKX_REF` or `TASKX_VERSION` is required, plus either `TASKX_GIT_URL` or `TASKX_OWNER`+`TASKX_REPO`*

### Verification

The installer always verifies the installation (unless `--verify-only` is used) by running:

1. **Smoke test:** `taskx --help`
2. **Health check:** `taskx doctor --timestamp-mode deterministic`

If either fails, the installer exits non-zero.

### Integration Examples

#### In a Makefile

```makefile
.PHONY: install-taskx
install-taskx:
	@export TASKX_OWNER=myorg && \
	 export TASKX_REPO=taskx && \
	 export TASKX_VERSION=0.3.0 && \
	 bash scripts/install_taskx.sh

.PHONY: verify-taskx
verify-taskx:
	@bash scripts/install_taskx.sh --verify-only
```

#### In CI/CD

```yaml
# GitHub Actions
- name: Install TaskX
  env:
    TASKX_OWNER: myorg
    TASKX_REPO: taskx
    TASKX_VERSION: 0.3.0
  run: bash scripts/install_taskx.sh --mode git

- name: Verify TaskX
  run: bash scripts/install_taskx.sh --verify-only
```

#### In a setup script

```bash
#!/bin/bash
# setup_project.sh

set -e

# Install TaskX
export TASKX_OWNER=myorg
export TASKX_REPO=taskx
export TASKX_VERSION=0.3.0

bash scripts/install_taskx.sh

# Use TaskX
taskx compile-tasks --mode mvp
taskx run-task --task-id T001
```

### Troubleshooting

#### Lockfile parse error

```
[ERROR] Invalid lockfile syntax at line: 'verison = 0.3.0'
```

**Fix:** Check spelling (should be `version`, not `verison`)

```
[ERROR] Unknown key in lockfile: 'verison'. Allowed keys: version ref mode owner repo git_url index_url extra_index_url
```

**Fix:** Use only allowed keys (prevents silent typos)

```
[ERROR] Invalid version format: '0.3'. Must be X.Y.Z (e.g., 0.3.0)
```

**Fix:** Use full semantic version: `0.3.0` not `0.3`

#### Auto-detection fails

```
[ERROR] Cannot auto-detect install mode. Please set one of:
  - TASKX_PKG_TOKEN (for GitHub Packages)
  - TASKX_OWNER + TASKX_REPO or TASKX_GIT_URL (for Git install)
  - TASKX_LOCAL_PATH (for local editable install)
```

**Fix:** Set required environment variables for your desired mode, or use `--mode` explicitly.

#### Git authentication fails

```
[ERROR] taskx @ git+ssh://git@github.com/myorg/taskx.git@v0.3.0
fatal: could not read from remote repository
```

**Fix:** 
- Ensure SSH keys are configured: `ssh -T git@github.com`
- Or use HTTPS with token in URL or credential helper

#### Doctor fails after install

```
[ERROR] taskx doctor failed. Installation is not healthy.
```

**Fix:**
- Check doctor output for specific failures
- Common issue: schema bundling (see "Schema Bundling Issues" section above)
- Verify you're installing a correctly built wheel/package

## Repo Discovery (Automatic Repo Finder)

When managing TaskX across many projects, use the repo discovery tool to automatically find all repositories containing `TASKX_VERSION.lock` under a given directory. This eliminates manual repo list curation.

### Quick Usage

```bash
# Discover all TaskX-enabled repos under ~/code
bash scripts/taskx_discover_repos.sh --root ~/code --depth 5

# Review discovered repos
cat out/taskx_repo_discovery/REPOS.txt
cat out/taskx_repo_discovery/DISCOVERY_REPORT.md
```

### Command Reference

```bash
bash scripts/taskx_discover_repos.sh [options]
```

**Required:**
- `--root <dir>` - Root directory to scan

**Optional:**
- `--out <dir>` - Output directory (default: `./out/taskx_repo_discovery`)
- `--depth <int>` - Max directory depth from root (default: `6`)
- `--max-repos <int>` - Hard cap on repos found (default: `200`)
- `--include-non-git` - Include repos without `.git/` directory (default: `true`)
- `--symlinks` - Follow symlinks during scan (default: `false`, **dangerous**)
- `--timestamp-mode deterministic|wallclock` - Timestamp mode (default: `deterministic`)

### Behavior

**Discovery Criteria (Strict):**

A directory is considered a "candidate repo" if it contains:
- `TASKX_VERSION.lock` at its root (exact filename match)

Optional classification (for reporting only):
- `git_repo = true` if directory contains `.git/` subdirectory

**No other heuristics.** Discovery is purely rule-based.

**Safety Features:**
- Does not follow symlinks by default (prevents infinite loops)
- Hard limit on scan depth (prevents deep tree traversal)
- Hard cap on max repos (prevents output explosion)
- Deterministic ordering (repos sorted lexicographically)

### Output Structure

```
out/taskx_repo_discovery/
├── REPOS.txt                    # One repo path per line (sorted)
├── discovery_raw.json           # Machine-friendly intermediate data
├── DISCOVERY_REPORT.json        # Structured report
└── DISCOVERY_REPORT.md          # Human-readable report
```

### DISCOVERY_REPORT.json Schema

```json
{
  "schema_version": "1.0",
  "generated_at": "1970-01-01T00:00:00Z",
  "timestamp_mode": "deterministic",
  "root": "/Users/username/code",
  "depth": 5,
  "max_repos": 200,
  "include_non_git": true,
  "symlinks": false,
  "summary": {
    "repos_found": 12,
    "repos_emitted": 12,
    "truncated": false
  },
  "repos": [
    {
      "path": "/Users/username/code/project1",
      "has_lockfile": true,
      "git_repo": true,
      "notes": []
    }
  ]
}
```

### DISCOVERY_REPORT.md Report

The Markdown report includes:

- **Metadata:** Scan root, depth, max repos, symlink mode
- **Summary:** Counts of repos found/emitted, truncation status
- **Warnings:** Truncation alerts, symlink mode warnings
- **Repository List:** Table with git status (first/last 20 if >50 repos)
- **Statistics:** Git vs non-git repo counts
- **Next Steps:** Copy-paste commands for audit and upgrade workflows

### Examples

#### Discover Repos for Multi-Repo Management

```bash
# 1. Discover all repos with TaskX
bash scripts/taskx_discover_repos.sh --root ~/code --depth 5

# 2. Review what was found
cat out/taskx_repo_discovery/DISCOVERY_REPORT.md

# 3. Audit for version drift
bash scripts/taskx_pin_audit.sh \
  --target-version 0.3.1 \
  --repo-list out/taskx_repo_discovery/REPOS.txt

# 4. Upgrade behind repos
bash scripts/taskx_upgrade_many.sh \
  --version 0.3.1 \
  --repo-list out/taskx_repo_discovery/REPOS.txt \
  --apply
```

#### Discover with Custom Limits

```bash
# Scan deeper with higher cap
bash scripts/taskx_discover_repos.sh \
  --root ~/projects \
  --depth 8 \
  --max-repos 500
```

#### Check Specific Workspace

```bash
# Scan a specific workspace directory
bash scripts/taskx_discover_repos.sh \
  --root /workspace \
  --depth 3 \
  --timestamp-mode deterministic
```

### Workflow Integration

**Before bulk upgrades:**

```bash
# 1. Discover all repos
bash scripts/taskx_discover_repos.sh --root ~/code --depth 5

# 2. Audit version drift (identifies who needs upgrade)
bash scripts/taskx_pin_audit.sh \
  --target-version 0.4.0 \
  --repo-list out/taskx_repo_discovery/REPOS.txt

# 3. Review audit report
cat out/taskx_pin_audit/PIN_AUDIT.md

# 4. Upgrade behind repos
bash scripts/taskx_upgrade_many.sh \
  --version 0.4.0 \
  --repo-list out/taskx_repo_discovery/REPOS.txt \
  --apply

# 5. Re-audit to confirm
bash scripts/taskx_pin_audit.sh \
  --target-version 0.4.0 \
  --repo-list out/taskx_repo_discovery/REPOS.txt
```

**Periodic version drift monitoring:**

```bash
# Weekly/monthly check
bash scripts/taskx_discover_repos.sh --root ~/code --depth 5
bash scripts/taskx_pin_audit.sh \
  --target-version $(cat CURRENT_TASKX_VERSION) \
  --repo-list out/taskx_repo_discovery/REPOS.txt

# If drift detected, investigate and upgrade
```

### Understanding Results

**repos_found vs repos_emitted:**
- `repos_found` = Total matching repos discovered
- `repos_emitted` = Repos actually written to REPOS.txt
- If `repos_found > max_repos`, output is truncated and `truncated = true`

**Git repo classification:**
- ✅ = Contains `.git/` directory (standard git repo)
- ❌ = No `.git/` directory (lockfile exists but not a git repo)

### Troubleshooting

#### No repos found

```
Repos found: 0
```

**Fix:**
- Verify root directory exists and is readable
- Check that repos actually contain `TASKX_VERSION.lock` files
- Increase `--depth` if repos are nested deeper
- Verify filename is exact: `TASKX_VERSION.lock` (case-sensitive)

#### Truncated output

```
Warning: Found 250 repos, truncating to 200
```

**Fix:** Increase `--max-repos`:

```bash
bash scripts/taskx_discover_repos.sh \
  --root ~/code \
  --depth 5 \
  --max-repos 500
```

#### Scan hangs or is very slow

**Fix:**
- Reduce `--depth` to limit directory traversal
- Add `--max-repos` to cap early
- Avoid scanning network mounts or large directories
- **Never use `--symlinks` unless absolutely necessary**

#### Duplicate repos in list

**Fix:**
- Discovery automatically deduplicates by path
- If seeing duplicates, check for symlinks (should not follow by default)
- Verify `REPOS.txt` content directly

## Pin Audit (Version Drift Scanner)

Before upgrading TaskX across projects, use the pin audit tool to scan for version drift and identify which repositories need attention.

### Quick Usage

```bash
# Audit all repos against target version
bash scripts/taskx_pin_audit.sh \
  --target-version 0.3.1 \
  --repo-list my_projects.txt
```

Output shows:
- Which repos are **behind** target (need upgrade)
- Which repos are **ahead** of target (already upgraded)
- Which repos are **missing lockfile**
- Which repos have **invalid version** format

### Command Reference

```bash
bash scripts/taskx_pin_audit.sh [flags]
```

**Required flags:**
- `--target-version X.Y.Z` - Target version to compare against
- Either:
  - `--repos <paths>` - Comma-separated repo paths
  - `--repo-list <file>` - File with one repo path per line

**Optional flags:**
- `--target-ref <ref>` - Target ref (default: `vX.Y.Z`)
- `--out <dir>` - Output directory (default: `./out/taskx_pin_audit`)
- `--timestamp-mode deterministic|wallclock` - Timestamp mode (default: `deterministic`)
- `--include-missing-lock` - Include repos without lockfiles in report

### Behavior

For each repository:

1. **Reads lockfile** (`TASKX_VERSION.lock`)
2. **Parses configuration** using same rules as installer
3. **Compares version** to target (semantic versioning)
4. **Checks ref match** (if present)
5. **Detects problems:**
   - Missing lockfile
   - Invalid version format
   - Unknown keys (warning)
   - Missing required fields

**Read-only:** Never modifies any files.

### Version Statuses

- **match** - Version equals target (✅)
- **behind** - Version < target (⚠️ needs upgrade)
- **ahead** - Version > target (ℹ️ informational)
- **missing_lock** - No lockfile found (❌)
- **invalid_version** - Version not parseable (❌)
- **unknown** - Version field missing (❓)

### Output Structure

```
out/taskx_pin_audit/
├── PIN_AUDIT.json           # Structured report
├── PIN_AUDIT.md             # Human-readable report
└── audit_raw.json           # Per-repo audit data
```

### PIN_AUDIT.json Schema

```json
{
  "schema_version": "1.0",
  "generated_at": "1970-01-01T00:00:00Z",
  "timestamp_mode": "deterministic",
  "target": {
    "version": "0.3.1",
    "ref": "v0.3.1"
  },
  "summary": {
    "repos_total": 10,
    "match": 7,
    "behind": 2,
    "ahead": 0,
    "missing_lock": 1,
    "invalid_version": 0,
    "unknown": 0
  },
  "repos": [
    {
      "path": "/path/to/project1",
      "status": "behind",
      "pinned": {
        "version": "0.3.0",
        "ref": "v0.3.0",
        "mode": "git"
      },
      "ref_match": false,
      "problems": [],
      "unknown_keys": [],
      "suggested_action": "upgrade to target via taskx_upgrade_many"
    }
  ]
}
```

### PIN_AUDIT.md Report

The Markdown report includes:

- **Summary:** Counts by status
- **Behind Repos Table:** Repos needing upgrade
- **Missing Lockfile:** Repos without lockfiles
- **Invalid Version:** Repos with malformed versions
- **Ahead Repos:** Repos already on newer versions
- **All Results Table:** Complete status overview
- **How to Fix:** Actionable upgrade commands
- **Next Actions:** Workflow steps

### Examples

#### Audit Current State

```bash
bash scripts/taskx_pin_audit.sh \
  --target-version 0.3.1 \
  --repo-list my_projects.txt

# Review report
cat out/taskx_pin_audit/PIN_AUDIT.md
```

#### Audit Before Upgrade

```bash
# 1. Discover all repos with TaskX
bash scripts/taskx_discover_repos.sh --root ~/code --depth 5

# 2. Audit against target version
bash scripts/taskx_pin_audit.sh \
  --target-version 0.3.1 \
  --repo-list out/taskx_repo_discovery/REPOS.txt

# 3. Review which repos need upgrade
cat out/taskx_pin_audit/PIN_AUDIT.md

# 4. Upgrade behind repos
bash scripts/taskx_upgrade_many.sh \
  --version 0.3.1 \
  --repo-list out/taskx_repo_discovery/REPOS.txt \
  --apply

# 5. Re-audit to verify
bash scripts/taskx_pin_audit.sh \
  --target-version 0.3.1 \
  --repo-list out/taskx_repo_discovery/REPOS.txt
```

#### Check Specific Repos

```bash
bash scripts/taskx_pin_audit.sh \
  --target-version 0.3.1 \
  --repos ~/dev/proj1,~/dev/proj2,~/dev/proj3
```

#### Include Missing Lockfiles

```bash
# Show all repos, even those without lockfiles
bash scripts/taskx_pin_audit.sh \
  --target-version 0.3.1 \
  --repo-list all_repos.txt \
  --include-missing-lock
```

### Workflow Integration

**Before major upgrade:**

```bash
# 1. Audit to see current state
bash scripts/taskx_pin_audit.sh --target-version 0.4.0 --repo-list repos.txt

# 2. Review PIN_AUDIT.md to identify issues
cat out/taskx_pin_audit/PIN_AUDIT.md

# 3. Fix missing/invalid lockfiles manually

# 4. Run upgrade for behind repos
bash scripts/taskx_upgrade_many.sh --version 0.4.0 --repo-list repos.txt --apply

# 5. Re-audit to confirm
bash scripts/taskx_pin_audit.sh --target-version 0.4.0 --repo-list repos.txt
```

**Periodic version drift check:**

```bash
# Weekly/monthly check for drift
bash scripts/taskx_pin_audit.sh \
  --target-version $(cat CURRENT_TASKX_VERSION) \
  --repo-list all_projects.txt

# If any repos are behind, investigate why
```

### Understanding Results

**Status: behind**
- Repository is running older version
- **Action:** Upgrade using `taskx_upgrade_many.sh`
- **Priority:** High (should be addressed)

**Status: match**
- Repository is at target version
- **Action:** None needed
- **Priority:** N/A

**Status: ahead**
- Repository is running newer version
- **Action:** Verify compatibility, or bump target
- **Priority:** Low (informational)

**Status: missing_lock**
- Repository has no `TASKX_VERSION.lock`
- **Action:** Create lockfile (use template)
- **Priority:** High (prevents version management)

**Status: invalid_version**
- Version field is malformed (e.g., `0.3` instead of `0.3.0`)
- **Action:** Fix to X.Y.Z format
- **Priority:** High (blocks automated tools)

**Status: unknown**
- Version field is missing from lockfile
- **Action:** Add version field
- **Priority:** High (blocks automated tools)

### Troubleshooting

#### Empty audit report

```
[INFO] Auditing 0 repositories...
```

**Fix:** Check repo list file is not empty and paths are correct.

#### All repos show "missing_lock"

```
Status: ❌ missing_lock (all repos)
```

**Fix:** Ensure you've initialized lockfiles. Run this in each repo:

```bash
cat > TASKX_VERSION.lock <<EOF
version = 0.3.0
mode = git
owner = myorg
repo = taskx
EOF
```

#### "Invalid version format" errors

```
Status: ❌ invalid_version
Version: 0.3
```

**Fix:** Use full semantic version: `version = 0.3.0` not `version = 0.3`

## Multi-Repo Upgrader

When managing TaskX across multiple projects, use the multi-repo upgrader to update all lockfiles and verify installations in a single operation.

### Quick Usage

**Dry-run (no changes):**
```bash
bash scripts/taskx_upgrade_many.sh \
  --version 0.3.1 \
  --repos /path/to/project1,/path/to/project2 \
  --timestamp-mode deterministic
```

**Apply updates and verify:**
```bash
bash scripts/taskx_upgrade_many.sh \
  --version 0.3.1 \
  --repo-list my_projects.txt \
  --apply
```

**Apply updates and install:**
```bash
bash scripts/taskx_upgrade_many.sh \
  --version 0.3.1 \
  --repo-list my_projects.txt \
  --apply \
  --install
```

### Command Reference

```bash
bash scripts/taskx_upgrade_many.sh [flags]
```

**Required flags:**
- `--version X.Y.Z` - Target TaskX version (strict semver)
- Either:
  - `--repos <paths>` - Comma-separated repo paths
  - `--repo-list <file>` - File with one repo path per line

**Optional flags:**
- `--ref <ref>` - Git ref (default: `vX.Y.Z`)
- `--mode auto|packages|git|local` - Install mode (default: `auto`)
- `--apply` - Apply changes (default: dry-run)
- `--install` - Run full install (default: verify-only)
- `--out <dir>` - Output directory (default: `./out/taskx_upgrade_many`)
- `--timestamp-mode deterministic|wallclock` - Timestamp mode (default: `deterministic`)

### Behavior

For each repository, the upgrader:

1. **Updates lockfile:**
   - Sets `version = X.Y.Z`
   - Sets `ref = <ref>` (default: `vX.Y.Z`)
   - Optionally sets `mode = <mode>`
   - Preserves comments and unknown keys
   - In dry-run: reports what would change

2. **Runs installer:**
   - Default: `bash scripts/install_taskx.sh --verify-only`
   - With `--install`: `bash scripts/install_taskx.sh`
   - Captures stdout/stderr to log file

3. **Generates report:**
   - Per-repo `result.json`
   - Rollup `ROLLUP.json` and `ROLLUP.md`
   - Sorted by path (deterministic)

### Repo List File Format

Create a text file with one absolute path per line:

```
# my_projects.txt
/Users/dev/project1
/Users/dev/project2
/Users/dev/project3

# Comments and blank lines are ignored
/Users/dev/project4
```

### Output Structure

```
out/taskx_upgrade_many/
├── ROLLUP.json              # Structured report
├── ROLLUP.md                # Human-readable report
├── project1/
│   ├── result.json          # Per-repo result
│   └── install.log          # Installer output
├── project2/
│   ├── result.json
│   └── install.log
└── project3/
    ├── result.json
    └── install.log
```

### ROLLUP.json Schema

```json
{
  "schema_version": "1.0",
  "generated_at": "1970-01-01T00:00:00Z",
  "timestamp_mode": "deterministic",
  "target_version": "0.3.1",
  "target_ref": "v0.3.1",
  "summary": {
    "repos_total": 3,
    "repos_passed": 2,
    "repos_failed": 1,
    "repos_skipped": 0
  },
  "repos": [
    {
      "path": "/path/to/project1",
      "status": "passed",
      "lockfile_updated": true,
      "install_mode": "verify-only",
      "installer_exit_code": 0,
      "notes": [],
      "logs": {
        "install_log_path": "/path/to/out/project1/install.log"
      }
    }
  ]
}
```

### ROLLUP.md Report

The Markdown report includes:

- **Summary:** Total repos, passed, failed, skipped
- **Results Table:** Status, mode, exit codes for all repos
- **Failures Section:** Detailed diagnostics for failed repos
- **Remediation:** Actionable steps to fix issues
- **Next Actions:** Commands to re-run for failed repos

### Examples

#### Dry-Run Across Projects

```bash
# See what would change, no modifications
bash scripts/taskx_upgrade_many.sh \
  --version 0.3.1 \
  --repos ~/dev/proj1,~/dev/proj2,~/dev/proj3
```

Output:
```
[INFO] Processing 3 repositories...
[INFO] Processing: /Users/dev/proj1
[INFO]   [DRY-RUN] Would update version=0.3.1 ref=v0.3.1
[INFO]   Running installer (mode: verify-only)...
[INFO]   ✅ Installer succeeded
```

#### Apply and Verify

```bash
# Update lockfiles and verify TaskX works
bash scripts/taskx_upgrade_many.sh \
  --version 0.3.1 \
  --repo-list my_projects.txt \
  --apply
```

This:
- Updates all `TASKX_VERSION.lock` files
- Runs `taskx doctor` in each repo
- Generates rollup report

#### Apply and Full Install

```bash
# Update lockfiles and reinstall TaskX
bash scripts/taskx_upgrade_many.sh \
  --version 0.3.1 \
  --repo-list my_projects.txt \
  --apply \
  --install
```

Use this after a major TaskX upgrade.

#### GitHub Packages Mode

```bash
# Upgrade using GitHub Packages
export TASKX_PKG_TOKEN=ghp_your_token

bash scripts/taskx_upgrade_many.sh \
  --version 0.3.1 \
  --mode packages \
  --repo-list my_projects.txt \
  --apply
```

Token is passed through to installer but never logged.

#### Custom Ref

```bash
# Upgrade to specific commit or branch
bash scripts/taskx_upgrade_many.sh \
  --version 0.3.1 \
  --ref main \
  --repo-list my_projects.txt \
  --apply
```

### Handling Failures

When some repos fail, the upgrader:

1. **Continues processing** all repos (doesn't stop on first failure)
2. **Logs details** to per-repo install.log
3. **Generates rollup** with failure diagnostics
4. **Exits non-zero** if any repo failed

**Review failures:**

```bash
# Check the rollup report
cat out/taskx_upgrade_many/ROLLUP.md

# Review specific failure log
cat out/taskx_upgrade_many/project_name/install.log
```

**Re-run failed repos only:**

The `ROLLUP.md` includes a ready-to-use command for re-running just the failed repos.

### Common Workflows

#### Initial Rollout to All Projects

```bash
# 1. Create repo list
find ~/dev -name "TASKX_VERSION.lock" -exec dirname {} \; > all_taskx_projects.txt

# 2. Dry-run to preview
bash scripts/taskx_upgrade_many.sh \
  --version 0.3.0 \
  --repo-list all_taskx_projects.txt

# 3. Review output, then apply
bash scripts/taskx_upgrade_many.sh \
  --version 0.3.0 \
  --repo-list all_taskx_projects.txt \
  --apply

# 4. Review rollup report
cat out/taskx_upgrade_many/ROLLUP.md
```

#### Upgrading to New Version

```bash
# 1. Update to 0.3.1 with verification
bash scripts/taskx_upgrade_many.sh \
  --version 0.3.1 \
  --repo-list my_projects.txt \
  --apply

# 2. If all pass, commit lockfile changes
for repo in $(cat my_projects.txt); do
  cd "$repo"
  git add TASKX_VERSION.lock
  git commit -m "chore: upgrade TaskX to 0.3.1"
  cd -
done
```

#### Testing Pre-Release

```bash
# 1. Upgrade to release candidate
bash scripts/taskx_upgrade_many.sh \
  --version 0.4.0 \
  --ref v0.4.0-rc1 \
  --repo-list my_projects.txt \
  --apply \
  --install

# 2. Test each project
# ...

# 3. Revert if needed or upgrade to stable
bash scripts/taskx_upgrade_many.sh \
  --version 0.4.0 \
  --ref v0.4.0 \
  --repo-list my_projects.txt \
  --apply \
  --install
```

### Troubleshooting

#### Doctor failures

```
❌ Installer failed (exit code: 2)
```

Check the install.log:
```bash
cat out/taskx_upgrade_many/project_name/install.log
```

Common causes:
- Schema bundling issues → update TaskX wheel
- Missing dependencies → install required packages

#### Missing install script

```
❌ Installer failed (exit code: 127)
bash: scripts/install_taskx.sh: No such file or directory
```

Fix: Copy `scripts/install_taskx.sh` to the project that's missing it.

#### Permission errors

```
❌ Failed to cd to /path/to/repo
```

Fix: Check directory permissions and paths.

## Repo Guard (Prevents Wrong-Repo Runs)

TaskX commands that modify state (`gate-allowlist`, `promote`, `ci-gate`) require running in a TaskX repository to prevent accidental execution in the wrong project.

### How It Works

TaskX detects repositories by searching for:
1. `.taskxroot` file (recommended - explicit marker)
2. `pyproject.toml` with `[project].name = "taskx"` (fallback)

The guard walks up the directory tree from your current location until it finds one of these markers or reaches the filesystem root.

### Setup (One-Time per Repo)

Mark your TaskX repository:

```bash
cd ~/code/taskX  # Navigate to your TaskX repo
touch .taskxroot
git add .taskxroot
git commit -m "chore: add TaskX repo marker"
```

### Guarded Commands

These commands **require** TaskX repo detection:
- `taskx gate-allowlist` - Stateful compliance gate
- `taskx promote-run` - Issues promotion tokens
- `taskx ci-gate` - CI/CD gate checks

These commands **do not** require repo detection:
- `taskx doctor` - Portable health check (runs anywhere)
- `taskx compile-tasks` - Can run in any repo
- All other commands - No state modification

### Override (Use with Caution)

```bash
# This will warn but proceed
taskx gate-allowlist --run ./out/runs/RUN_001 --no-repo-guard
```

### Troubleshooting

#### Error: TaskX repo not detected

**Fix Option 1 (Recommended):**
```bash
cd /path/to/your/taskx/repo
touch .taskxroot
```

**Fix Option 2 (Bypass):**
```bash
taskx gate-allowlist --run ./out/runs/RUN_001 --no-repo-guard
```

## Clean Venv Verification (Recommended Before Release)

Verify that TaskX builds correctly and passes all health checks in a clean environment:

```bash
cd ~/code/taskX
bash scripts/taskx_verify_clean_venv.sh
```

**What it checks:**
1. ✅ Clean venv creation
2. ✅ Build tools installation
3. ✅ TaskX wheel build
4. ✅ Wheel installation
5. ✅ `taskx --version` works
6. ✅ `taskx doctor` passes (from /tmp, no repo)

**When to run:**
- Before cutting a release
- After changing build configuration
- After modifying schema bundling
- When investigating installation issues

## Additional Resources

- **TaskX Doctor:** Run `taskx doctor --help`
- **TaskX CI Gate:** Run `taskx ci-gate --help`
- **GitHub Releases:** https://github.com/OWNER/REPO/releases
- **Report Issues:** https://github.com/OWNER/REPO/issues

---

**Note:** Replace `OWNER/REPO` throughout this document with your actual GitHub repository path.
