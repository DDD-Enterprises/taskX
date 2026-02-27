#!/bin/bash
set -e

echo "Starting Google Jules, Copilot, Codex, and Claude Code Cloud setup..."

# Install dopeTask
pip install -e .

# Initialize Project
echo "Initializing dopeTask project..."
dopetask project init --out .

# Initialize Route Availability
echo "Initializing route availability..."
dopetask route init --repo-root . --force

echo "Setup complete. Verifying availability configuration..."
cat .dopetask/runtime/availability.yaml

echo "Ready to serve."
