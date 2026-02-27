# dopeTask Installation Guide

## Install dopeTask into Another Repository

dopeTask provides a simple, pinned installation mechanism for consumer repositories (like Dopemux, ChatX, etc.) without vendoring source code.

### Quick Start (Automatic)

The easiest way to install dopeTask into your repository is using the unified installer script. This will set up a virtual environment and install dopeTask.

**1. One-Liner Install:**

Run this from your repository root:

```bash
curl -fsSL https://raw.githubusercontent.com/hu3mann/dopeTask/main/scripts/install.sh | bash
```

This will:
- Detect your repository root.
- Create a `.dopetask-pin` file (defaulting to the latest `main` version) if one doesn't exist.
- Create a virtual environment (`.dopetask_venv` or reuse `.venv`).
- Install dopeTask.

**2. Verify installation:**

```bash
source .dopetask_venv/bin/activate  # or .venv/bin/activate
dopetask doctor --timestamp-mode deterministic
```

### Advanced Installation

You can customize the installation by providing arguments to the script or creating a `.dopetask-pin` file manually.

**Install a specific version:**

```bash
curl -fsSL https://raw.githubusercontent.com/hu3mann/dopeTask/main/scripts/install.sh | bash -s -- --version v0.2.0
```

**Install from PyPI:**

```bash
curl -fsSL https://raw.githubusercontent.com/hu3mann/dopeTask/main/scripts/install.sh | bash -s -- --pypi
```

**Manual Pin Configuration:**

Create `.dopetask-pin` before running the installer:

```bash
cat > .dopetask-pin <<'EOF'
install=git
repo=https://github.com/hu3mann/dopeTask.git
ref=v0.1.0
EOF

curl -fsSL https://raw.githubusercontent.com/hu3mann/dopeTask/main/scripts/install.sh | bash
```

### Repo Shell Wiring (`project shell`)

dopeTask can bootstrap repo-local shell wiring so `dopetask` resolves deterministically inside a repository:

```bash
dopetask project shell init --repo-root .
dopetask project shell status --repo-root .
```

`init` creates (without overwriting existing files):
- `.envrc` with `export PATH="$(pwd)/scripts:$PATH"`
- `scripts/dopetask` shim
- `scripts/dopetask-local` launcher

### Upgrading dopeTask

dopeTask now includes a self-upgrade command.

**Upgrade to the latest version:**

```bash
dopetask upgrade --latest
```

**Upgrade/Downgrade to a specific version:**

```bash
dopetask upgrade --version v0.2.0
```

These commands will automatically update your `.dopetask-pin` file and reinstall the package.

### Pin File Format

The `.dopetask-pin` file defines which dopeTask version to install. Place it at your repository root.

#### Option 1: Git Tag

Install from a specific git tag:

```
install=git
repo=https://github.com/hu3mann/dopeTask.git
ref=v0.1.0
```

#### Option 2: PyPI (Recommended)

Install from PyPI:

```
install=pypi
ref=0.1.0
```

#### Option 3: Local Wheel

Install from a local wheel file:

```
install=wheel
path=dist/dopetask-0.1.0-py3-none-any.whl
```

### Virtual Environment

The installer creates or uses a virtual environment:

**Priority:**
1. If `.venv` exists -> use it
2. Otherwise -> create `.dopetask_venv`

**Activate:**
```bash
source .venv/bin/activate
# or
source .dopetask_venv/bin/activate
```
