#!/usr/bin/env bash
# A16_MIN.12 — Repo Discovery (Find TaskX-Pinned Repos + Emit Repo List)
#
# Discovers repositories containing TASKX_VERSION.lock under a given root directory
# and emits a deterministic repo list file usable by taskx_upgrade_many.sh and taskx_pin_audit.sh.
#
# Usage:
#   bash scripts/taskx_discover_repos.sh --root /path/to/search [options]

set -euo pipefail

# ================================================================================
# DEFAULTS
# ================================================================================

ROOT_DIR=""
OUT_DIR="./out/taskx_repo_discovery"
DEPTH=6
MAX_REPOS=200
INCLUDE_NON_GIT=true
FOLLOW_SYMLINKS=false
TIMESTAMP_MODE="deterministic"

# ================================================================================
# ARGUMENT PARSING
# ================================================================================

while [[ $# -gt 0 ]]; do
  case "$1" in
    --root)
      ROOT_DIR="$2"
      shift 2
      ;;
    --out)
      OUT_DIR="$2"
      shift 2
      ;;
    --depth)
      DEPTH="$2"
      shift 2
      ;;
    --max-repos)
      MAX_REPOS="$2"
      shift 2
      ;;
    --include-non-git)
      INCLUDE_NON_GIT=true
      shift
      ;;
    --symlinks)
      FOLLOW_SYMLINKS=true
      shift
      ;;
    --timestamp-mode)
      TIMESTAMP_MODE="$2"
      shift 2
      ;;
    *)
      echo "Error: Unknown flag '$1'"
      echo "Usage: $0 --root <dir> [--out <dir>] [--depth <int>] [--max-repos <int>] [--include-non-git] [--symlinks] [--timestamp-mode deterministic|wallclock]"
      exit 1
      ;;
  esac
done

# ================================================================================
# VALIDATION
# ================================================================================

if [[ -z "$ROOT_DIR" ]]; then
  echo "Error: --root is required"
  echo "Usage: $0 --root <dir> [options]"
  exit 1
fi

if [[ ! -d "$ROOT_DIR" ]]; then
  echo "Error: Root directory does not exist: $ROOT_DIR"
  exit 1
fi

# Normalize root to absolute path
ROOT_DIR=$(cd "$ROOT_DIR" && pwd)

# ================================================================================
# UTILITY FUNCTIONS
# ================================================================================

log() {
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*"
}

get_timestamp() {
  if [[ "$TIMESTAMP_MODE" == "deterministic" ]]; then
    echo "1970-01-01T00:00:00Z"
  else
    date -u +%Y-%m-%dT%H:%M:%SZ
  fi
}

# ================================================================================
# DISCOVERY
# ================================================================================

log "Starting repo discovery"
log "Root: $ROOT_DIR"
log "Depth: $DEPTH"
log "Max repos: $MAX_REPOS"
log "Include non-git: $INCLUDE_NON_GIT"
log "Follow symlinks: $FOLLOW_SYMLINKS"

# Create output directory
mkdir -p "$OUT_DIR"

# Build find command
FIND_OPTS=()
FIND_OPTS+=("-maxdepth" "$DEPTH")
FIND_OPTS+=("-name" "TASKX_VERSION.lock")
FIND_OPTS+=("-type" "f")

if [[ "$FOLLOW_SYMLINKS" == "false" ]]; then
  FIND_OPTS=("-P" "${FIND_OPTS[@]}")  # Don't follow symlinks
fi

log "Scanning for TASKX_VERSION.lock files..."

# Find all lockfiles and extract parent directories (repo roots)
TEMP_REPOS=$(mktemp)
trap "rm -f $TEMP_REPOS" EXIT

# Use find to locate lockfiles
find "$ROOT_DIR" "${FIND_OPTS[@]}" 2>/dev/null | while IFS= read -r lockfile; do
  # Get parent directory (repo root)
  repo_path=$(dirname "$lockfile")
  echo "$repo_path"
done | sort -u > "$TEMP_REPOS"

REPOS_FOUND=$(wc -l < "$TEMP_REPOS" | tr -d ' ')
log "Found $REPOS_FOUND repos with TASKX_VERSION.lock"

# ================================================================================
# TRUNCATION & REPO LIST
# ================================================================================

TRUNCATED=false
REPOS_EMITTED=$REPOS_FOUND

if (( REPOS_FOUND > MAX_REPOS )); then
  log "Warning: Found $REPOS_FOUND repos, truncating to $MAX_REPOS"
  TRUNCATED=true
  REPOS_EMITTED=$MAX_REPOS
  head -n "$MAX_REPOS" "$TEMP_REPOS" > "$OUT_DIR/REPOS.txt"
else
  cp "$TEMP_REPOS" "$OUT_DIR/REPOS.txt"
fi

log "Emitting $REPOS_EMITTED repos to REPOS.txt"

# ================================================================================
# GENERATE DISCOVERY RAW JSON
# ================================================================================

TIMESTAMP=$(get_timestamp)

log "Generating discovery_raw.json..."

cat > "$OUT_DIR/discovery_raw.json" <<EOF
{
  "schema_version": "1.0",
  "generated_at": "$TIMESTAMP",
  "timestamp_mode": "$TIMESTAMP_MODE",
  "root": "$ROOT_DIR",
  "depth": $DEPTH,
  "max_repos": $MAX_REPOS,
  "include_non_git": $INCLUDE_NON_GIT,
  "symlinks": $FOLLOW_SYMLINKS,
  "summary": {
    "repos_found": $REPOS_FOUND,
    "repos_emitted": $REPOS_EMITTED,
    "truncated": $TRUNCATED
  },
  "repos": [
EOF

# Read emitted repos and generate JSON array
FIRST=true
while IFS= read -r repo_path; do
  # Check if repo has .git directory
  GIT_REPO=false
  if [[ -d "$repo_path/.git" ]]; then
    GIT_REPO=true
  fi
  
  # Filter non-git if requested
  if [[ "$INCLUDE_NON_GIT" == "false" && "$GIT_REPO" == "false" ]]; then
    continue
  fi
  
  # Build JSON object
  if [[ "$FIRST" == "false" ]]; then
    echo "," >> "$OUT_DIR/discovery_raw.json"
  fi
  FIRST=false
  
  cat >> "$OUT_DIR/discovery_raw.json" <<REPO_EOF
    {
      "path": "$repo_path",
      "has_lockfile": true,
      "git_repo": $GIT_REPO,
      "notes": []
    }
REPO_EOF
done < "$OUT_DIR/REPOS.txt"

# Close JSON array
cat >> "$OUT_DIR/discovery_raw.json" <<EOF

  ]
}
EOF

log "discovery_raw.json written"

# ================================================================================
# CALL PYTHON REPORT GENERATOR
# ================================================================================

log "Generating reports via Python..."

PYTHON_CMD="${PYTHON:-python3}"

if ! command -v "$PYTHON_CMD" &> /dev/null; then
  PYTHON_CMD="python"
fi

if ! command -v "$PYTHON_CMD" &> /dev/null; then
  log "Error: Python not found. Cannot generate reports."
  exit 1
fi

"$PYTHON_CMD" scripts/taskx_discover_repos_report.py \
  --in "$OUT_DIR/discovery_raw.json" \
  --out "$OUT_DIR" \
  --timestamp-mode "$TIMESTAMP_MODE"

# ================================================================================
# SUMMARY
# ================================================================================

log "Discovery complete"
log "Repos found: $REPOS_FOUND"
log "Repos emitted: $REPOS_EMITTED"
log "Truncated: $TRUNCATED"
log "Output directory: $OUT_DIR"
log ""
log "Files created:"
log "  - REPOS.txt ($REPOS_EMITTED lines)"
log "  - discovery_raw.json"
log "  - DISCOVERY_REPORT.json"
log "  - DISCOVERY_REPORT.md"
log ""
log "Next steps:"
log "  # Review discovered repos"
log "  cat $OUT_DIR/DISCOVERY_REPORT.md"
log ""
log "  # Audit version drift"
log "  bash scripts/taskx_pin_audit.sh --target-version X.Y.Z --repo-list $OUT_DIR/REPOS.txt"
log ""
log "  # Upgrade repos"
log "  bash scripts/taskx_upgrade_many.sh --version X.Y.Z --repo-list $OUT_DIR/REPOS.txt --apply"
