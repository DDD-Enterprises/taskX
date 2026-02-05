#!/usr/bin/env bash
# TaskX Pin Audit
# Read-only scanner for TASKX_VERSION.lock version drift

set -euo pipefail

# ============================================================================
# Configuration & Defaults
# ============================================================================

TARGET_VERSION=""
TARGET_REF=""
REPOS=""
REPO_LIST=""
OUT_DIR="./out/taskx_pin_audit"
TIMESTAMP_MODE="deterministic"
INCLUDE_MISSING_LOCK=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --target-version)
      TARGET_VERSION="$2"
      shift 2
      ;;
    --target-ref)
      TARGET_REF="$2"
      shift 2
      ;;
    --repos)
      REPOS="$2"
      shift 2
      ;;
    --repo-list)
      REPO_LIST="$2"
      shift 2
      ;;
    --out)
      OUT_DIR="$2"
      shift 2
      ;;
    --timestamp-mode)
      TIMESTAMP_MODE="$2"
      shift 2
      ;;
    --include-missing-lock)
      INCLUDE_MISSING_LOCK=true
      shift
      ;;
    *)
      echo "[ERROR] Unknown flag: $1" >&2
      exit 1
      ;;
  esac
done

# ============================================================================
# Validation
# ============================================================================

if [[ -z "$TARGET_VERSION" ]]; then
  echo "[ERROR] --target-version is required" >&2
  exit 1
fi

if [[ -z "$REPOS" && -z "$REPO_LIST" ]]; then
  echo "[ERROR] Either --repos or --repo-list is required" >&2
  exit 1
fi

if [[ -n "$REPOS" && -n "$REPO_LIST" ]]; then
  echo "[ERROR] Cannot use both --repos and --repo-list" >&2
  exit 1
fi

# Validate target version format
if [[ ! "$TARGET_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "[ERROR] Invalid target version format: '$TARGET_VERSION'. Must be X.Y.Z" >&2
  exit 1
fi

# Default target ref if not provided
if [[ -z "$TARGET_REF" ]]; then
  TARGET_REF="v${TARGET_VERSION}"
fi

# ============================================================================
# Utility Functions
# ============================================================================

log_info() {
  echo "[INFO] $*"
}

log_warn() {
  echo "[WARN] $*"
}

log_error() {
  echo "[ERROR] $*" >&2
}

get_timestamp() {
  if [[ "$TIMESTAMP_MODE" == "deterministic" ]]; then
    echo "1970-01-01T00:00:00Z"
  else
    date -u +"%Y-%m-%dT%H:%M:%SZ"
  fi
}

# Allowed lockfile keys (same as installer)
ALLOWED_LOCKFILE_KEYS=(
  "version"
  "ref"
  "mode"
  "owner"
  "repo"
  "git_url"
  "index_url"
  "extra_index_url"
)

is_valid_lockfile_key() {
  local key="$1"
  for allowed in "${ALLOWED_LOCKFILE_KEYS[@]}"; do
    if [[ "$key" == "$allowed" ]]; then
      return 0
    fi
  done
  return 1
}

# Compare semantic versions (X.Y.Z triplets only)
# Returns: -1 (v1 < v2), 0 (equal), 1 (v1 > v2), 2 (invalid)
compare_versions() {
  local v1="$1"
  local v2="$2"
  
  # Validate both are X.Y.Z format
  if [[ ! "$v1" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "2"
    return
  fi
  
  if [[ ! "$v2" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "2"
    return
  fi
  
  # Split into components
  IFS='.' read -r v1_major v1_minor v1_patch <<< "$v1"
  IFS='.' read -r v2_major v2_minor v2_patch <<< "$v2"
  
  # Compare major
  if (( v1_major < v2_major )); then
    echo "-1"
    return
  elif (( v1_major > v2_major )); then
    echo "1"
    return
  fi
  
  # Compare minor
  if (( v1_minor < v2_minor )); then
    echo "-1"
    return
  elif (( v1_minor > v2_minor )); then
    echo "1"
    return
  fi
  
  # Compare patch
  if (( v1_patch < v2_patch )); then
    echo "-1"
    return
  elif (( v1_patch > v2_patch )); then
    echo "1"
    return
  fi
  
  # Equal
  echo "0"
}

# ============================================================================
# Lockfile Parsing
# ============================================================================

audit_repo() {
  local repo_path="$1"
  local lockfile="$repo_path/TASKX_VERSION.lock"
  
  local pinned_version=""
  local pinned_ref=""
  local pinned_mode=""
  local pinned_owner=""
  local pinned_repo=""
  local pinned_git_url=""
  local pinned_index_url=""
  local pinned_extra_index_url=""
  
  local problems=()
  local unknown_keys=()
  local status=""
  local ref_match="null"
  local suggested_action=""
  
  # Check if lockfile exists
  if [[ ! -f "$lockfile" ]]; then
    status="missing_lock"
    suggested_action="create lockfile (A16_MIN.10 template)"
    problems+=("lockfile not found")
    
    # Output JSON for this repo
    local problems_json
    problems_json=$(printf '%s\n' "${problems[@]}" | jq -R . | jq -s .)
    local unknown_keys_json="[]"
    
    cat <<EOF
{
  "path": "$repo_path",
  "status": "$status",
  "pinned": {
    "version": null,
    "ref": null,
    "mode": null
  },
  "ref_match": null,
  "problems": $problems_json,
  "unknown_keys": $unknown_keys_json,
  "suggested_action": "$suggested_action"
}
EOF
    return
  fi
  
  # Parse lockfile
  while IFS= read -r line || [[ -n "$line" ]]; do
    # Strip whitespace
    line="$(echo "$line" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
    
    # Skip blank lines and comments
    [[ -z "$line" ]] && continue
    [[ "$line" =~ ^# ]] && continue
    
    # Parse key = value
    if [[ "$line" =~ ^([a-z_]+)[[:space:]]*=[[:space:]]*(.*)$ ]]; then
      local key="${BASH_REMATCH[1]}"
      local value="${BASH_REMATCH[2]}"
      
      # Trim value
      value="$(echo "$value" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
      
      # Check if key is valid
      if ! is_valid_lockfile_key "$key"; then
        unknown_keys+=("$key")
        continue
      fi
      
      # Extract known keys
      case "$key" in
        version)
          pinned_version="$value"
          ;;
        ref)
          pinned_ref="$value"
          ;;
        mode)
          pinned_mode="$value"
          ;;
        owner)
          pinned_owner="$value"
          ;;
        repo)
          pinned_repo="$value"
          ;;
        git_url)
          pinned_git_url="$value"
          ;;
        index_url)
          pinned_index_url="$value"
          ;;
        extra_index_url)
          pinned_extra_index_url="$value"
          ;;
      esac
    fi
  done < "$lockfile"
  
  # Analyze version
  if [[ -z "$pinned_version" ]]; then
    status="unknown"
    suggested_action="add version to lockfile"
    problems+=("version field missing")
  else
    # Validate version format
    if [[ ! "$pinned_version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
      status="invalid_version"
      suggested_action="fix lockfile version format to X.Y.Z"
      problems+=("invalid version format: $pinned_version")
    else
      # Compare to target
      local cmp_result
      cmp_result=$(compare_versions "$pinned_version" "$TARGET_VERSION")
      
      case "$cmp_result" in
        -1)
          status="behind"
          suggested_action="upgrade to target via taskx_upgrade_many"
          ;;
        0)
          status="match"
          suggested_action="none"
          ;;
        1)
          status="ahead"
          suggested_action="verify compatibility; consider pinning down or bumping target"
          ;;
        2)
          status="invalid_version"
          suggested_action="fix lockfile version format to X.Y.Z"
          problems+=("version comparison failed")
          ;;
      esac
    fi
  fi
  
  # Check ref match
  if [[ -n "$pinned_ref" && -n "$TARGET_REF" ]]; then
    if [[ "$pinned_ref" == "$TARGET_REF" ]]; then
      ref_match="true"
    else
      ref_match="false"
    fi
  fi
  
  # Report unknown keys as warnings (not fatal)
  if [[ ${#unknown_keys[@]} -gt 0 ]]; then
    problems+=("unknown keys found: ${unknown_keys[*]}")
  fi
  
  # Build JSON output
  local problems_json
  problems_json=$(printf '%s\n' "${problems[@]}" | jq -R . | jq -s .)
  
  local unknown_keys_json
  unknown_keys_json=$(printf '%s\n' "${unknown_keys[@]}" | jq -R . | jq -s .)
  
  local version_json="null"
  [[ -n "$pinned_version" ]] && version_json="\"$pinned_version\""
  
  local ref_json="null"
  [[ -n "$pinned_ref" ]] && ref_json="\"$pinned_ref\""
  
  local mode_json="null"
  [[ -n "$pinned_mode" ]] && mode_json="\"$pinned_mode\""
  
  cat <<EOF
{
  "path": "$repo_path",
  "status": "$status",
  "pinned": {
    "version": $version_json,
    "ref": $ref_json,
    "mode": $mode_json
  },
  "ref_match": $ref_match,
  "problems": $problems_json,
  "unknown_keys": $unknown_keys_json,
  "suggested_action": "$suggested_action"
}
EOF
}

# ============================================================================
# Main
# ============================================================================

main() {
  log_info "TaskX Pin Audit"
  log_info "==============="
  log_info "Target version: $TARGET_VERSION"
  log_info "Target ref: $TARGET_REF"
  log_info "Output: $OUT_DIR"
  log_info "Timestamp mode: $TIMESTAMP_MODE"
  log_info ""
  
  # Create output directory
  mkdir -p "$OUT_DIR"
  
  # Build repo list
  local repo_paths=()
  
  if [[ -n "$REPOS" ]]; then
    # Parse comma-separated repos
    IFS=',' read -ra repo_paths <<< "$REPOS"
  else
    # Read from file
    if [[ ! -f "$REPO_LIST" ]]; then
      log_error "Repo list file not found: $REPO_LIST"
      exit 1
    fi
    
    while IFS= read -r line || [[ -n "$line" ]]; do
      # Skip blank lines and comments
      [[ -z "$line" ]] && continue
      [[ "$line" =~ ^# ]] && continue
      
      repo_paths+=("$line")
    done < "$REPO_LIST"
  fi
  
  # Dedupe and sort (deterministic)
  local sorted_repos
  sorted_repos=$(printf '%s\n' "${repo_paths[@]}" | sort -u)
  
  mapfile -t repo_paths <<< "$sorted_repos"
  
  log_info "Auditing ${#repo_paths[@]} repositories..."
  log_info ""
  
  # Audit each repo
  local audit_raw="$OUT_DIR/audit_raw.json"
  echo "[" > "$audit_raw"
  
  local first=true
  for repo_path in "${repo_paths[@]}"; do
    [[ -z "$repo_path" ]] && continue
    
    log_info "Auditing: $repo_path"
    
    if [[ ! -d "$repo_path" ]]; then
      log_warn "  Repo not found, skipping"
      continue
    fi
    
    # Add comma separator
    if [[ "$first" == "false" ]]; then
      echo "," >> "$audit_raw"
    fi
    first=false
    
    # Audit and append JSON
    audit_repo "$repo_path" >> "$audit_raw"
  done
  
  echo "" >> "$audit_raw"
  echo "]" >> "$audit_raw"
  
  log_info ""
  log_info "Generating reports..."
  
  # Generate reports
  if command -v python3 &> /dev/null; then
    python3 scripts/taskx_pin_audit_report.py \
      --audit-file "$audit_raw" \
      --target-version "$TARGET_VERSION" \
      --target-ref "$TARGET_REF" \
      --out-dir "$OUT_DIR" \
      --timestamp-mode "$TIMESTAMP_MODE"
    
    log_info "✅ Pin audit complete:"
    log_info "  - $OUT_DIR/PIN_AUDIT.json"
    log_info "  - $OUT_DIR/PIN_AUDIT.md"
  else
    log_warn "python3 not found - skipping report generation"
    log_warn "To generate report manually, run:"
    log_warn "  python3 scripts/taskx_pin_audit_report.py --audit-file $audit_raw --target-version $TARGET_VERSION --target-ref $TARGET_REF --out-dir $OUT_DIR --timestamp-mode $TIMESTAMP_MODE"
  fi
  
  log_info ""
  log_info "Review: $OUT_DIR/PIN_AUDIT.md"
}

main "$@"
