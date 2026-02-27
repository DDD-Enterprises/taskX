#!/usr/bin/env python3
"""
dopeTask Pin Audit Report Generator
Reads audit_raw.json and generates PIN_AUDIT.json + PIN_AUDIT.md
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


def get_timestamp(timestamp_mode: str) -> str:
    """Get timestamp based on mode."""
    if timestamp_mode == "deterministic":
        return "1970-01-01T00:00:00Z"
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def load_audit_data(audit_file: Path) -> List[Dict[str, Any]]:
    """Load audit_raw.json."""
    try:
        with open(audit_file, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"[ERROR] Failed to load {audit_file}: {e}", file=sys.stderr)
        sys.exit(1)


def generate_pin_audit_json(
    audit_data: List[Dict[str, Any]],
    target_version: str,
    target_ref: str,
    timestamp_mode: str
) -> Dict[str, Any]:
    """Generate PIN_AUDIT.json content."""
    
    # Count by status
    total = len(audit_data)
    match = sum(1 for r in audit_data if r.get("status") == "match")
    behind = sum(1 for r in audit_data if r.get("status") == "behind")
    ahead = sum(1 for r in audit_data if r.get("status") == "ahead")
    missing_lock = sum(1 for r in audit_data if r.get("status") == "missing_lock")
    invalid_version = sum(1 for r in audit_data if r.get("status") == "invalid_version")
    unknown = sum(1 for r in audit_data if r.get("status") == "unknown")
    
    return {
        "schema_version": "1.0",
        "generated_at": get_timestamp(timestamp_mode),
        "timestamp_mode": timestamp_mode,
        "target": {
            "version": target_version,
            "ref": target_ref
        },
        "summary": {
            "repos_total": total,
            "match": match,
            "behind": behind,
            "ahead": ahead,
            "missing_lock": missing_lock,
            "invalid_version": invalid_version,
            "unknown": unknown
        },
        "repos": sorted(audit_data, key=lambda x: x.get("path", ""))
    }


def generate_pin_audit_md(pin_audit_json: Dict[str, Any], out_dir: Path) -> str:
    """Generate PIN_AUDIT.md content."""
    
    target = pin_audit_json["target"]
    summary = pin_audit_json["summary"]
    repos = pin_audit_json["repos"]
    
    md_lines = [
        "# dopeTask Pin Audit Report",
        "",
        f"**Target Version:** {target['version']}  ",
        f"**Target Ref:** {target['ref']}  ",
        f"**Generated:** {pin_audit_json['generated_at']}  ",
        f"**Timestamp Mode:** {pin_audit_json['timestamp_mode']}  ",
        "",
        "## Summary",
        "",
        f"- **Total Repositories:** {summary['repos_total']}",
        f"- **Match Target:** {summary['match']} ✅",
        f"- **Behind Target:** {summary['behind']} ⚠️",
        f"- **Ahead of Target:** {summary['ahead']} ℹ️",
        f"- **Missing Lockfile:** {summary['missing_lock']} ❌",
        f"- **Invalid Version:** {summary['invalid_version']} ❌",
        f"- **Unknown Version:** {summary['unknown']} ❓",
        "",
    ]
    
    # Overall status
    if summary["behind"] == 0 and summary["missing_lock"] == 0 and summary["invalid_version"] == 0:
        md_lines.extend([
            "**Overall Status:** ✅ All repositories are at target version or newer",
            "",
        ])
    else:
        issues = summary["behind"] + summary["missing_lock"] + summary["invalid_version"]
        md_lines.extend([
            f"**Overall Status:** ⚠️ {issues} repositories need attention",
            "",
        ])
    
    # Behind repos (most important)
    behind_repos = [r for r in repos if r["status"] == "behind"]
    
    if behind_repos:
        md_lines.extend([
            "## Repositories Behind Target",
            "",
            "These repositories are running older versions and should be upgraded:",
            "",
            "| Repository | Current Version | Target Version | Ref Match |",
            "|------------|-----------------|----------------|-----------|",
        ])
        
        for repo in behind_repos:
            repo_name = Path(repo["path"]).name
            current_ver = repo["pinned"]["version"] or "unknown"
            ref_match_icon = "✅" if repo.get("ref_match") is True else ("❌" if repo.get("ref_match") is False else "―")
            
            md_lines.append(
                f"| `{repo_name}` | {current_ver} | {target['version']} | {ref_match_icon} |"
            )
        
        md_lines.extend(["", ""])
    
    # Missing lockfile
    missing_repos = [r for r in repos if r["status"] == "missing_lock"]
    
    if missing_repos:
        md_lines.extend([
            "## Missing Lockfile",
            "",
            "These repositories do not have a `DOPETASK_VERSION.lock` file:",
            "",
        ])
        
        for repo in missing_repos:
            md_lines.append(f"- `{repo['path']}`")
        
        md_lines.extend([
            "",
            "**Action:** Create lockfiles using the template from A16_MIN.10.",
            "",
        ])
    
    # Invalid version
    invalid_repos = [r for r in repos if r["status"] == "invalid_version" or r["status"] == "unknown"]
    
    if invalid_repos:
        md_lines.extend([
            "## Invalid or Unknown Version",
            "",
            "These repositories have lockfiles with invalid or missing version fields:",
            "",
        ])
        
        for repo in invalid_repos:
            current_ver = repo["pinned"]["version"] or "<missing>"
            md_lines.append(f"- `{Path(repo['path']).name}`: version = {current_ver}")
        
        md_lines.extend([
            "",
            "**Action:** Fix version field to use X.Y.Z format.",
            "",
        ])
    
    # Ahead repos (informational)
    ahead_repos = [r for r in repos if r["status"] == "ahead"]
    
    if ahead_repos:
        md_lines.extend([
            "## Repositories Ahead of Target",
            "",
            "These repositories are running newer versions than the target:",
            "",
        ])
        
        for repo in ahead_repos:
            repo_name = Path(repo["path"]).name
            current_ver = repo["pinned"]["version"]
            md_lines.append(f"- `{repo_name}`: {current_ver}")
        
        md_lines.extend([
            "",
            "**Action:** Verify compatibility or consider bumping the target version.",
            "",
        ])
    
    # Detailed results table
    md_lines.extend([
        "## All Repository Results",
        "",
        "| Repository | Status | Version | Ref | Mode |",
        "|------------|--------|---------|-----|------|",
    ])
    
    status_icons = {
        "match": "✅",
        "behind": "⚠️",
        "ahead": "ℹ️",
        "missing_lock": "❌",
        "invalid_version": "❌",
        "unknown": "❓"
    }
    
    for repo in repos:
        repo_name = Path(repo["path"]).name
        status_icon = status_icons.get(repo["status"], "❓")
        version = repo["pinned"]["version"] or "―"
        ref = repo["pinned"]["ref"] or "―"
        mode = repo["pinned"]["mode"] or "―"
        
        md_lines.append(
            f"| `{repo_name}` | {status_icon} {repo['status']} | {version} | {ref} | {mode} |"
        )
    
    md_lines.extend(["", ""])
    
    # How to fix section
    if summary["behind"] > 0 or summary["missing_lock"] > 0 or summary["invalid_version"] > 0:
        md_lines.extend([
            "## How to Fix",
            "",
            "### Upgrade Behind Repositories",
            "",
            "Use the multi-repo upgrader to update all behind repositories:",
            "",
            "```bash",
            "# 1. Create list of behind repos (or use existing repo list)",
            "cat > behind_repos.txt <<EOF",
        ])
        
        for repo in behind_repos:
            md_lines.append(repo["path"])
        
        md_lines.extend([
            "EOF",
            "",
            "# 2. Run upgrader",
            f"bash scripts/dopetask_upgrade_many.sh --version {target['version']} \\",
            "  --repo-list behind_repos.txt \\",
            "  --apply --install",
            "```",
            "",
            "### Create Missing Lockfiles",
            "",
            "For repositories without lockfiles, create them manually:",
            "",
            "```bash",
            "# For each missing repo, create DOPETASK_VERSION.lock:",
            "cat > DOPETASK_VERSION.lock <<EOF",
            f"version = {target['version']}",
            f"ref = {target['ref']}",
            "mode = git",
            "owner = YOUR_ORG",
            "repo = YOUR_REPO",
            "EOF",
            "```",
            "",
            "### Fix Invalid Versions",
            "",
            "Edit lockfiles with invalid version formats to use X.Y.Z:",
            "",
            "```bash",
            "# Correct format:",
            "version = 0.3.1  # Not: version = 0.3 or version = v0.3.1",
            "```",
            "",
        ])
    
    # Next actions
    md_lines.extend([
        "## Next Actions",
        "",
    ])
    
    if summary["behind"] == 0 and summary["missing_lock"] == 0 and summary["invalid_version"] == 0:
        md_lines.extend([
            "All repositories are properly configured! 🎉",
            "",
            "**Monitor for drift:**",
            "",
            "```bash",
            "# Re-run audit periodically",
            f"bash scripts/dopetask_pin_audit.sh --target-version {target['version']} \\",
            "  --repo-list your_repos.txt",
            "```",
            "",
        ])
    else:
        md_lines.extend([
            "1. **Fix issues** identified in sections above",
            "2. **Run upgrade** using `dopetask_upgrade_many.sh`",
            "3. **Re-audit** to verify all repos are updated:",
            "",
            "```bash",
            f"bash scripts/dopetask_pin_audit.sh --target-version {target['version']} \\",
            "  --repo-list your_repos.txt",
            "```",
            "",
        ])
    
    md_lines.extend([
        "---",
        "",
        f"**Report Location:** `{out_dir}/PIN_AUDIT.md`  ",
        f"**JSON Report:** `{out_dir}/PIN_AUDIT.json`  ",
        f"**Raw Audit Data:** `{out_dir}/audit_raw.json`  ",
    ])
    
    return "\n".join(md_lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate dopeTask pin audit report"
    )
    parser.add_argument(
        "--audit-file",
        type=Path,
        required=True,
        help="Path to audit_raw.json"
    )
    parser.add_argument(
        "--target-version",
        required=True,
        help="Target dopeTask version"
    )
    parser.add_argument(
        "--target-ref",
        required=True,
        help="Target git ref"
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        required=True,
        help="Output directory"
    )
    parser.add_argument(
        "--timestamp-mode",
        choices=["deterministic", "wallclock"],
        default="deterministic",
        help="Timestamp mode"
    )
    
    args = parser.parse_args()
    
    if not args.audit_file.exists():
        print(f"[ERROR] Audit file not found: {args.audit_file}", file=sys.stderr)
        sys.exit(1)
    
    # Load audit data
    audit_data = load_audit_data(args.audit_file)
    
    # Generate JSON report
    pin_audit_json = generate_pin_audit_json(
        audit_data,
        args.target_version,
        args.target_ref,
        args.timestamp_mode
    )
    
    json_path = args.out_dir / "PIN_AUDIT.json"
    with open(json_path, "w") as f:
        json.dump(pin_audit_json, f, indent=2)
    
    print(f"[INFO] Generated: {json_path}")
    
    # Generate Markdown report
    pin_audit_md = generate_pin_audit_md(pin_audit_json, args.out_dir)
    
    md_path = args.out_dir / "PIN_AUDIT.md"
    with open(md_path, "w") as f:
        f.write(pin_audit_md)
    
    print(f"[INFO] Generated: {md_path}")
    
    # Print summary to console
    summary = pin_audit_json["summary"]
    print("")
    print("[INFO] Audit Summary:")
    print(f"  Total: {summary['repos_total']}")
    print(f"  Match: {summary['match']}")
    print(f"  Behind: {summary['behind']}")
    print(f"  Ahead: {summary['ahead']}")
    print(f"  Missing: {summary['missing_lock']}")
    print(f"  Invalid: {summary['invalid_version']}")
    
    # Exit with status
    if summary["behind"] > 0 or summary["missing_lock"] > 0 or summary["invalid_version"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
