#!/usr/bin/env bash
# dopeTask Multi-Repo Upgrader
# Updates DOPETASK_VERSION.lock across multiple repos and verifies/installs dopeTask

set -euo pipefail

# ============================================================================
# Configuration & Defaults
# ============================================================================

VERSION=""
REF=""
REPOS=""
REPO_LIST=""
MODE="auto"
APPLY=false
INSTALL=false
OUT_DIR="./out/dopetask_upgrade_many"
TIMESTAMP_MODE="deterministic"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --version)
      VERSION="$2"
      shift 2
      ;;
    --ref)
      REF="$2"
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
    --mode)
      MODE="$2"
      shift 2
      ;;
    --apply)
      APPLY=true
      shift
      ;;
    --install)
      INSTALL=true
      shift
      ;;
    --out)
      OUT_DIR="$2"
      shift 2
      ;;
    --timestamp-mode)
      TIMESTAMP_MODE="$2"
      shift 2
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

if [[ -z "$VERSION" ]]; then
  echo "[ERROR] --version is required" >&2
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

# Validate version format
if [[ ! "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "[ERROR] Invalid version format: '$VERSION'. Must be X.Y.Z" >&2
  exit 1
fi

# Default ref if not provided
if [[ -z "$REF" ]]; then
  REF="v${VERSION}"
fi

# ============================================================================
# Utility Functions
# ============================================================================

log_info() {
  echo "[INFO] $*"
}

log_error() {
  echo "[ERROR] $*" >&2
}

log_warn() {
  echo "[WARN] $*"
}

get_timestamp() {
  if [[ "$TIMESTAMP_MODE" == "deterministic" ]]; then
    echo "1970-01-01T00:00:00Z"
  else
    date -u +"%Y-%m-%dT%H:%M:%SZ"
  fi
}

# Generate stable hash for collision resolution
get_path_hash() {
  local path="$1"
  echo -n "$path" | md5sum 2>/dev/null | cut -d' ' -f1 | head -c8 || echo "00000000"
}

# Get repo basename with collision handling
get_repo_dirname() {
  local repo_path="$1"
  local out_base="$2"
  
  local basename
  basename=$(basename "$repo_path")
  
  # Check if directory already exists
  if [[ -d "$out_base/$basename" ]]; then
    # Collision - append hash
    local hash
    hash=$(get_path_hash "$repo_path")
    basename="${basename}_${hash}"
  fi
  
  echo "$basename"
}

# ============================================================================
# Lockfile Update
# ============================================================================

update_lockfile() {
  local repo_path="$1"
  local lockfile="$repo_path/DOPETASK_VERSION.lock"
  local dry_run="$2"
  
  if [[ ! -f "$lockfile" ]]; then
    if [[ "$dry_run" == "true" ]]; then
      log_info "  [DRY-RUN] Would create $lockfile"
      return 0
    else
      log_info "  Creating new lockfile"
      cat > "$lockfile" <<EOF
# dopeTask install pin for this repo
# Created by dopetask_upgrade_many.sh on $(date -u +"%Y-%m-%d %H:%M:%S UTC")

version = $VERSION
ref = $REF
EOF
      if [[ "$MODE" != "auto" ]]; then
        echo "mode = $MODE" >> "$lockfile"
      fi
      return 0
    fi
  fi
  
  # Lockfile exists - update in place
  if [[ "$dry_run" == "true" ]]; then
    log_info "  [DRY-RUN] Would update version=$VERSION ref=$REF in $lockfile"
    return 0
  fi
  
  log_info "  Updating lockfile: version=$VERSION ref=$REF"
  
  # Create temp file
  local temp_file
  temp_file=$(mktemp)
  
  local version_updated=false
  local ref_updated=false
  local mode_updated=false
  
  # Read line by line, preserving comments and unknown keys
  while IFS= read -r line || [[ -n "$line" ]]; do
    # Check if this is a version line
    if [[ "$line" =~ ^[[:space:]]*version[[:space:]]*= ]]; then
      echo "version = $VERSION" >> "$temp_file"
      version_updated=true
    # Check if this is a ref line
    elif [[ "$line" =~ ^[[:space:]]*ref[[:space:]]*= ]]; then
      echo "ref = $REF" >> "$temp_file"
      ref_updated=true
    # Check if this is a mode line and we have a mode override
    elif [[ "$line" =~ ^[[:space:]]*mode[[:space:]]*= ]] && [[ "$MODE" != "auto" ]]; then
      echo "mode = $MODE" >> "$temp_file"
      mode_updated=true
    else
      # Preserve all other lines (comments, unknown keys, blank lines)
      echo "$line" >> "$temp_file"
    fi
  done < "$lockfile"
  
  # Append missing keys at end
  if [[ "$version_updated" == "false" ]]; then
    echo "version = $VERSION" >> "$temp_file"
  fi
  
  if [[ "$ref_updated" == "false" ]]; then
    echo "ref = $REF" >> "$temp_file"
  fi
  
  if [[ "$MODE" != "auto" && "$mode_updated" == "false" ]]; then
    echo "mode = $MODE" >> "$temp_file"
  fi
  
  # Replace original
  mv "$temp_file" "$lockfile"
}

# ============================================================================
# Per-Repo Processing
# ============================================================================

process_repo() {
  local repo_path="$1"
  local repo_out_dir="$2"
  
  log_info "Processing: $repo_path"
  
  # Validate repo exists
  if [[ ! -d "$repo_path" ]]; then
    log_error "  Repo not found: $repo_path"
    return 1
  fi
  
  # Create output directory
  mkdir -p "$repo_out_dir"
  
  local start_time
  start_time=$(get_timestamp)
  
  local notes=()
  local lockfile_found=false
  local lockfile_updated=false
  local installer_exit_code=0
  
  # Check if lockfile exists
  if [[ -f "$repo_path/DOPETASK_VERSION.lock" ]]; then
    lockfile_found=true
  fi
  
  # Update lockfile
  if [[ "$APPLY" == "true" ]]; then
    update_lockfile "$repo_path" "false"
    lockfile_updated=true
  else
    update_lockfile "$repo_path" "true"
    notes+=("dry-run: lockfile not modified")
  fi
  
  # Run installer
  local installer_mode="verify-only"
  if [[ "$INSTALL" == "true" ]]; then
    installer_mode="install"
  fi
  
  local install_log="$repo_out_dir/install.log"
  
  log_info "  Running installer (mode: $installer_mode)..."
  
  cd "$repo_path" || {
    log_error "  Failed to cd to $repo_path"
    installer_exit_code=1
    notes+=("failed to change directory")
  }
  
  if [[ $installer_exit_code -eq 0 ]]; then
    if [[ "$INSTALL" == "true" ]]; then
      bash scripts/install_dopetask.sh > "$install_log" 2>&1 || installer_exit_code=$?
    else
      bash scripts/install_dopetask.sh --verify-only > "$install_log" 2>&1 || installer_exit_code=$?
    fi
    
    if [[ $installer_exit_code -eq 0 ]]; then
      log_info "  ✅ Installer succeeded"
    else
      log_error "  ❌ Installer failed (exit code: $installer_exit_code)"
      notes+=("installer failed with exit code $installer_exit_code")
    fi
  fi
  
  local end_time
  end_time=$(get_timestamp)
  
  # Write result.json
  local status="passed"
  if [[ $installer_exit_code -ne 0 ]]; then
    status="failed"
  fi
  
  local notes_json
  notes_json=$(printf '%s\n' "${notes[@]}" | jq -R . | jq -s .)
  
  cat > "$repo_out_dir/result.json" <<EOF
{
  "path": "$repo_path",
  "lockfile_found": $lockfile_found,
  "lockfile_updated": $lockfile_updated,
  "apply_mode": $APPLY,
  "installer_mode": "$installer_mode",
  "installer_exit_code": $installer_exit_code,
  "start_time": "$start_time",
  "end_time": "$end_time",
  "notes": $notes_json,
  "install_log_path": "$install_log",
  "status": "$status"
}
EOF
  
  return $installer_exit_code
}

# ============================================================================
# Main
# ============================================================================

main() {
  log_info "dopeTask Multi-Repo Upgrader"
  log_info "=========================="
  log_info "Target version: $VERSION"
  log_info "Target ref: $REF"
  log_info "Mode: $MODE"
  log_info "Apply: $APPLY"
  log_info "Install: $INSTALL"
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
  
  log_info "Processing ${#repo_paths[@]} repositories..."
  log_info ""
  
  # Process each repo
  local failed_count=0
  
  for repo_path in "${repo_paths[@]}"; do
    # Get output directory name
    local repo_dirname
    repo_dirname=$(get_repo_dirname "$repo_path" "$OUT_DIR")
    local repo_out_dir="$OUT_DIR/$repo_dirname"
    
    if ! process_repo "$repo_path" "$repo_out_dir"; then
      ((failed_count++)) || true
    fi
    
    log_info ""
  done
  
  # Generate rollup report
  log_info "Generating rollup report..."
  
  if command -v python3 &> /dev/null; then
    python3 scripts/dopetask_upgrade_many_report.py \
      --out-dir "$OUT_DIR" \
      --version "$VERSION" \
      --ref "$REF" \
      --timestamp-mode "$TIMESTAMP_MODE"
    
    log_info "✅ Rollup report generated:"
    log_info "  - $OUT_DIR/ROLLUP.json"
    log_info "  - $OUT_DIR/ROLLUP.md"
  else
    log_warn "python3 not found - skipping report generation"
    log_warn "To generate report manually, run:"
    log_warn "  python3 scripts/dopetask_upgrade_many_report.py --out-dir $OUT_DIR --version $VERSION --ref $REF --timestamp-mode $TIMESTAMP_MODE"
  fi
  
  log_info ""
  log_info "=========================="
  
  if [[ $failed_count -eq 0 ]]; then
    log_info "🎉 All repositories processed successfully"
    exit 0
  else
    log_error "❌ $failed_count repositories failed"
    log_error "Review logs in: $OUT_DIR"
    exit 1
  fi
}

main "$@"
