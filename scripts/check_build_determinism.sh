#!/usr/bin/env bash
set -euo pipefail

export LC_ALL=C

tmpdir="$(mktemp -d "${TMPDIR:-/tmp}/taskx-determinism.XXXXXX")"
cleanup() {
  rm -rf "$tmpdir"
}
trap cleanup EXIT

hashes1="$tmpdir/hashes1.txt"
hashes2="$tmpdir/hashes2.txt"

# Reuse existing build artifacts as the first build output if available,
# so CI can call this right after uv build without tripling build time.
if ! ls dist/*.whl 1>/dev/null 2>&1; then
  uv build
fi
sha256sum dist/*.whl | sort > "$hashes1"

rm -rf dist
uv build
sha256sum dist/*.whl | sort > "$hashes2"

diff -u "$hashes1" "$hashes2"

echo "Deterministic wheel build verified."
