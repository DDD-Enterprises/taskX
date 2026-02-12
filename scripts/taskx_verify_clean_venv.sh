#!/usr/bin/env bash
# TaskX Clean Venv Verification Script
# Verifies TaskX builds correctly and passes doctor checks in a clean environment.

set -euo pipefail

# Configuration
VENV_PATH="${TASKX_VENV_PATH:-/tmp/taskx-verify-venv}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

# Cleanup function
cleanup() {
    if [[ -d "$VENV_PATH" ]]; then
        log_info "Cleaning up venv..."
        rm -rf "$VENV_PATH"
    fi
}

# Trap cleanup on exit
trap cleanup EXIT

# Main verification
main() {
    log_info "Starting TaskX clean venv verification..."
    log_info "Repo root: $REPO_ROOT"
    log_info "Venv path: $VENV_PATH"

    # Create clean venv
    log_info "Creating clean venv..."
    python3 -m venv "$VENV_PATH"
    source "$VENV_PATH/bin/activate"

    # Install build tools
    log_info "Installing build tools..."
    pip install --quiet --upgrade pip build || { log_error "Build tools install failed"; exit 1; }
    log_info "✅ Build tools installed"

    # Build TaskX
    log_info "Building TaskX..."
    cd "$REPO_ROOT"
    python -m build --quiet || { log_error "Build failed"; exit 1; }
    log_info "✅ Build successful"

    # Install wheel
    log_info "Installing TaskX wheel..."
    pip install --quiet --force-reinstall dist/*.whl || { log_error "Install failed"; exit 1; }
    log_info "✅ TaskX installed"

    # Verify installation
    log_info "Verifying TaskX installation..."
    taskx --version || { log_error "Version check failed"; exit 1; }
    log_info "✅ TaskX version check passed"

    # Run doctor from /tmp (portable check)
    log_info "Running doctor from /tmp (portable mode)..."
    (cd /tmp && taskx doctor --timestamp-mode deterministic) || {
        log_error "Doctor check failed"
        exit 1
    }
    log_info "✅ Doctor check passed"

    deactivate

    # Success!
    echo ""
    log_info "════════════════════════════════════════"
    log_info "✅ Clean venv verification PASSED"
    log_info "════════════════════════════════════════"
    echo ""
}

main "$@"
