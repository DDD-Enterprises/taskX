#!/usr/bin/env bash
# dopeTask Installer for Consumer Repos
# Installs dopeTask into another repository based on .dopetask-pin configuration

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

# Find repository root by walking up to find .git or pyproject.toml
find_repo_root() {
    local dir="$PWD"
    while [ "$dir" != "/" ]; do
        if [ -d "$dir/.git" ] || [ -f "$dir/pyproject.toml" ]; then
            echo "$dir"
            return 0
        fi
        dir="$(dirname "$dir")"
    done

    log_error "Could not find repository root (.git or pyproject.toml)"
    return 1
}

# Parse .dopetask-pin file
parse_pin_file() {
    local pin_file="$1"

    if [ ! -f "$pin_file" ]; then
        log_error ".dopetask-pin file not found at: $pin_file"
        log_error "Create one with:"
        log_error "  install=git"
        log_error "  repo=https://github.com/owner/repo.git"
        log_error "  ref=v0.1.0"
        exit 1
    fi

    # Read pin file and export variables
    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        [[ "$key" =~ ^#.*$ ]] && continue
        [[ -z "$key" ]] && continue

        # Trim whitespace
        key=$(echo "$key" | xargs)
        value=$(echo "$value" | xargs)

        case "$key" in
            install) INSTALL_METHOD="$value" ;;
            repo) REPO_URL="$value" ;;
            ref) REF="$value" ;;
            path) WHEEL_PATH="$value" ;;
            *) log_warn "Unknown key in .dopetask-pin: $key" ;;
        esac
    done < "$pin_file"

    # Validate required fields
    if [ -z "${INSTALL_METHOD:-}" ]; then
        log_error "Missing 'install' field in .dopetask-pin"
        exit 1
    fi

    if [ "$INSTALL_METHOD" = "git" ]; then
        if [ -z "${REPO_URL:-}" ]; then
            log_error "Missing 'repo' field for git install method"
            exit 1
        fi
        if [ -z "${REF:-}" ]; then
            log_error "Missing 'ref' field for git install method"
            exit 1
        fi
    elif [ "$INSTALL_METHOD" = "wheel" ]; then
        if [ -z "${WHEEL_PATH:-}" ]; then
            log_error "Missing 'path' field for wheel install method"
            exit 1
        fi
    else
        log_error "Invalid install method: $INSTALL_METHOD (must be 'git' or 'wheel')"
        exit 1
    fi
}

# Main installation logic
main() {
    log_info "dopeTask Consumer Repo Installer"
    echo ""

    # Find repository root
    log_info "Finding repository root..."
    REPO_ROOT=$(find_repo_root)
    log_info "Repository root: $REPO_ROOT"
    echo ""

    # Check for .dopetask-pin
    PIN_FILE="$REPO_ROOT/.dopetask-pin"
    log_info "Reading pin configuration from: $PIN_FILE"
    parse_pin_file "$PIN_FILE"
    echo ""

    # Determine venv location
    if [ -d "$REPO_ROOT/.venv" ]; then
        VENV_PATH="$REPO_ROOT/.venv"
        log_info "Using existing venv: $VENV_PATH"
    else
        VENV_PATH="$REPO_ROOT/.dopetask_venv"
        log_info "Creating venv: $VENV_PATH"
        python3 -m venv "$VENV_PATH"
    fi
    echo ""

    # Activate venv
    log_info "Activating venv..."
    source "$VENV_PATH/bin/activate"

    # Upgrade pip
    log_info "Upgrading pip..."
    pip install --quiet --upgrade pip
    echo ""

    # Install dopeTask based on method
    if [ "$INSTALL_METHOD" = "git" ]; then
        log_info "Installing dopeTask from git:"
        log_info "  Repository: $REPO_URL"
        log_info "  Reference: $REF"

        INSTALL_URL="git+${REPO_URL}@${REF}"
        pip install --force-reinstall "$INSTALL_URL"

    elif [ "$INSTALL_METHOD" = "wheel" ]; then
        # Handle relative paths
        if [[ "$WHEEL_PATH" != /* ]]; then
            WHEEL_PATH="$REPO_ROOT/$WHEEL_PATH"
        fi

        log_info "Installing dopeTask from wheel:"
        log_info "  Path: $WHEEL_PATH"

        if [ ! -f "$WHEEL_PATH" ]; then
            log_error "Wheel file not found: $WHEEL_PATH"
            exit 1
        fi

        pip install --force-reinstall "$WHEEL_PATH"
    fi
    echo ""

    # Verify installation
    log_info "Verifying dopeTask installation..."

    VERIFICATION_OUTPUT=$(python -c "
import sys
import dopetask
print(f'Version: {dopetask.__version__}')
print(f'Location: {dopetask.__file__}')

# Test schema loading
from dopetask.utils.schema_registry import SchemaRegistry
registry = SchemaRegistry()
schema = registry.get('allowlist_diff')
print(f'Schema loading: OK (loaded allowlist_diff)')
" 2>&1)

    if [ $? -eq 0 ]; then
        echo "$VERIFICATION_OUTPUT"
        echo ""
        log_info "✅ dopeTask installation successful!"
        echo ""
        log_info "To activate this environment:"
        log_info "  source $VENV_PATH/bin/activate"
        echo ""
        log_info "To verify dopeTask:"
        log_info "  dopetask doctor --timestamp-mode deterministic"
    else
        log_error "Verification failed!"
        echo "$VERIFICATION_OUTPUT"
        exit 1
    fi
}

main "$@"
