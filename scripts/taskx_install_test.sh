#!/usr/bin/env bash
# dopeTask install test - Creates temp venv, installs wheel, and runs doctor

set -euo pipefail

echo "=== dopeTask Install Test ==="

# Find the wheel file
WHEEL_FILE=$(find dist/ -name "*.whl" | head -n 1)

if [ -z "$WHEEL_FILE" ]; then
    echo "❌ Error: No wheel file found in dist/"
    exit 1
fi

echo "Testing wheel: $WHEEL_FILE"

# Create temporary venv
TEMP_VENV=$(mktemp -d -t dopetask-test-venv.XXXXXX)
echo "Creating temporary venv: $TEMP_VENV"

python -m venv "$TEMP_VENV"

# Activate venv
if [ -f "$TEMP_VENV/bin/activate" ]; then
    # Unix-like
    source "$TEMP_VENV/bin/activate"
elif [ -f "$TEMP_VENV/Scripts/activate" ]; then
    # Windows
    source "$TEMP_VENV/Scripts/activate"
else
    echo "❌ Error: Cannot find venv activation script"
    rm -rf "$TEMP_VENV"
    exit 1
fi

# Install wheel
echo "Installing wheel..."
pip install "$WHEEL_FILE" --quiet

# Test 1: dopetask --help
echo "Test 1: dopetask --help"
if ! dopetask --help > /dev/null 2>&1; then
    echo "❌ Error: dopetask --help failed"
    deactivate
    rm -rf "$TEMP_VENV"
    exit 1
fi
echo "✅ dopetask --help works"

# Test 2: dopetask doctor
echo "Test 2: dopetask doctor"
DOCTOR_OUT=$(mktemp -d -t dopetask-doctor-test.XXXXXX)

if ! dopetask doctor --timestamp-mode deterministic --out "$DOCTOR_OUT"; then
    echo "❌ Error: dopetask doctor failed"
    cat "$DOCTOR_OUT/DOCTOR_REPORT.md" || true
    deactivate
    rm -rf "$TEMP_VENV"
    rm -rf "$DOCTOR_OUT"
    exit 1
fi
echo "✅ dopetask doctor passed"

# Cleanup
deactivate
rm -rf "$TEMP_VENV"
rm -rf "$DOCTOR_OUT"

echo "✅ All install tests passed"
