#!/usr/bin/env python3
"""dopeTask Pin Audit Tool

Reads and validates .dopetask-pin configuration files.
"""

import sys
from pathlib import Path


def find_repo_root(start_dir: Path) -> Path | None:
    """Find repository root by walking up to find .git or pyproject.toml."""
    current = start_dir.resolve()
    while current != current.parent:
        if (current / ".git").exists() or (current / "pyproject.toml").exists():
            return current
        current = current.parent
    return None


def parse_pin_file(pin_file: Path) -> dict[str, str]:
    """Parse .dopetask-pin file into dictionary."""
    config = {}

    if not pin_file.exists():
        return config

    with open(pin_file, 'r') as f:
        for line in f:
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue

            # Parse key=value
            if '=' not in line:
                print(f"⚠️  Warning: Invalid line (no '='): {line}", file=sys.stderr)
                continue

            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()

            config[key] = value

    return config


def validate_config(config: dict[str, str], repo_root: Path) -> bool:
    """Validate pin configuration."""
    valid = True

    # Check install method
    if 'install' not in config:
        print("❌ Missing required field: install", file=sys.stderr)
        valid = False
    else:
        method = config['install']
        if method not in ('git', 'wheel'):
            print(f"❌ Invalid install method: {method} (must be 'git' or 'wheel')", file=sys.stderr)
            valid = False

        # Validate method-specific fields
        if method == 'git':
            if 'repo' not in config:
                print("❌ Missing required field for git install: repo", file=sys.stderr)
                valid = False
            if 'ref' not in config:
                print("❌ Missing required field for git install: ref", file=sys.stderr)
                valid = False

        elif method == 'wheel':
            if 'path' not in config:
                print("❌ Missing required field for wheel install: path", file=sys.stderr)
                valid = False
            else:
                # Check if wheel exists
                wheel_path = Path(config['path'])
                if not wheel_path.is_absolute():
                    wheel_path = repo_root / wheel_path

                if not wheel_path.exists():
                    print(f"⚠️  Warning: Wheel file not found: {wheel_path}", file=sys.stderr)

    return valid


def print_summary(config: dict[str, str], repo_root: Path) -> None:
    """Print normalized summary of pin configuration."""
    print("dopeTask Pin Configuration Summary")
    print("=" * 50)
    print(f"Repository root: {repo_root}")
    print()

    if not config:
        print("Status: ❌ No .dopetask-pin file found")
        return

    method = config.get('install', 'unknown')
    print(f"Install method: {method}")

    if method == 'git':
        repo = config.get('repo', '<missing>')
        ref = config.get('ref', '<missing>')
        print(f"Repository: {repo}")
        print(f"Reference: {ref}")
        print(f"Install target: git+{repo}@{ref}")

    elif method == 'wheel':
        path = config.get('path', '<missing>')
        wheel_path = Path(path)
        if not wheel_path.is_absolute():
            wheel_path = repo_root / wheel_path

        exists = "✅ exists" if wheel_path.exists() else "❌ not found"
        print(f"Wheel path: {path}")
        print(f"Resolved path: {wheel_path}")
        print(f"Status: {exists}")

    else:
        print("Status: ❌ Invalid or unknown install method")


def main() -> int:
    """Main entry point."""
    # Find repository root
    repo_root = find_repo_root(Path.cwd())

    if not repo_root:
        print("❌ Could not find repository root (.git or pyproject.toml)", file=sys.stderr)
        return 1

    # Find and parse pin file
    pin_file = repo_root / ".dopetask-pin"
    config = parse_pin_file(pin_file)

    if not config:
        print(f"❌ No .dopetask-pin file found at: {pin_file}", file=sys.stderr)
        print("\nCreate one with:", file=sys.stderr)
        print("  install=git", file=sys.stderr)
        print("  repo=https://github.com/owner/repo.git", file=sys.stderr)
        print("  ref=v0.1.0", file=sys.stderr)
        return 1

    # Validate configuration
    valid = validate_config(config, repo_root)

    # Print summary
    print_summary(config, repo_root)
    print()

    if valid:
        print("Status: ✅ Configuration valid")
        return 0
    else:
        print("Status: ❌ Configuration invalid")
        return 1


if __name__ == "__main__":
    sys.exit(main())
