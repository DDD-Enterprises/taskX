#!/usr/bin/env bash
# dopeTask build script - Builds sdist + wheel and validates with twine

set -euo pipefail

echo "=== dopeTask Build Script ==="
echo "Building distribution packages..."

# Ensure clean dist directory
if [ -d "dist" ]; then
    echo "Cleaning existing dist/ directory..."
    rm -rf dist/
fi

# Upgrade build tools
echo "Upgrading pip, build, and twine..."
python -m pip install -U pip build twine --quiet

# Build sdist and wheel
echo "Building sdist and wheel..."
python -m build

# Check that artifacts were created
if [ ! -d "dist" ] || [ -z "$(ls -A dist/)" ]; then
    echo "❌ Error: dist/ directory is empty after build"
    exit 1
fi

echo "Built packages:"
ls -lh dist/

# Validate with twine
echo "Validating packages with twine..."
python -m twine check dist/*

echo "✅ Build complete and validated"
