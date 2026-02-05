#!/usr/bin/env python3
"""
TaskX Multi-Repo Upgrade Report Generator
Reads per-repo result.json files and generates rollup reports
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


def load_repo_results(out_dir: Path) -> List[Dict[str, Any]]:
    """Load all result.json files from repo output directories."""
    results = []
    
    for repo_dir in out_dir.iterdir():
        if not repo_dir.is_dir():
            continue
        
        result_file = repo_dir / "result.json"
        if not result_file.exists():
            continue
        
        try:
            with open(result_file, "r") as f:
                result = json.load(f)
                results.append(result)
        except (json.JSONDecodeError, IOError) as e:
            print(f"[WARN] Failed to load {result_file}: {e}", file=sys.stderr)
            continue
    
    # Sort by path for determinism
    results.sort(key=lambda x: x.get("path", ""))
    
    return results


def generate_rollup_json(
    results: List[Dict[str, Any]],
    version: str,
    ref: str,
    timestamp_mode: str
) -> Dict[str, Any]:
    """Generate ROLLUP.json content."""
    
    total = len(results)
    passed = sum(1 for r in results if r.get("status") == "passed")
    failed = sum(1 for r in results if r.get("status") == "failed")
    skipped = sum(1 for r in results if r.get("status") == "skipped")
    
    repos_data = []
    for result in results:
        repos_data.append({
            "path": result.get("path", ""),
            "status": result.get("status", "unknown"),
            "lockfile_updated": result.get("lockfile_updated", False),
            "install_mode": result.get("installer_mode", "unknown"),
            "installer_exit_code": result.get("installer_exit_code", -1),
            "notes": result.get("notes", []),
            "logs": {
                "install_log_path": result.get("install_log_path", "")
            }
        })
    
    return {
        "schema_version": "1.0",
        "generated_at": get_timestamp(timestamp_mode),
        "timestamp_mode": timestamp_mode,
        "target_version": version,
        "target_ref": ref,
        "summary": {
            "repos_total": total,
            "repos_passed": passed,
            "repos_failed": failed,
            "repos_skipped": skipped
        },
        "repos": repos_data
    }


def generate_rollup_md(
    rollup_json: Dict[str, Any],
    out_dir: Path
) -> str:
    """Generate ROLLUP.md content."""
    
    summary = rollup_json["summary"]
    repos = rollup_json["repos"]
    
    md_lines = [
        "# TaskX Multi-Repo Upgrade Report",
        "",
        f"**Target Version:** {rollup_json['target_version']}  ",
        f"**Target Ref:** {rollup_json['target_ref']}  ",
        f"**Generated:** {rollup_json['generated_at']}  ",
        f"**Timestamp Mode:** {rollup_json['timestamp_mode']}  ",
        "",
        "## Summary",
        "",
        f"- **Total Repositories:** {summary['repos_total']}",
        f"- **Passed:** {summary['repos_passed']} ✅",
        f"- **Failed:** {summary['repos_failed']} ❌",
        f"- **Skipped:** {summary['repos_skipped']} ⏭️",
        "",
    ]
    
    # Overall status
    if summary["repos_failed"] == 0:
        md_lines.extend([
            "**Overall Status:** ✅ All repositories processed successfully",
            "",
        ])
    else:
        md_lines.extend([
            f"**Overall Status:** ❌ {summary['repos_failed']} repositories failed",
            "",
        ])
    
    # Results table
    md_lines.extend([
        "## Repository Results",
        "",
        "| Repository | Status | Mode | Exit Code | Lockfile Updated |",
        "|------------|--------|------|-----------|------------------|",
    ])
    
    for repo in repos:
        status_icon = {
            "passed": "✅",
            "failed": "❌",
            "skipped": "⏭️"
        }.get(repo["status"], "❓")
        
        lockfile_icon = "✅" if repo["lockfile_updated"] else "❌"
        
        md_lines.append(
            f"| `{Path(repo['path']).name}` | {status_icon} {repo['status']} | "
            f"{repo['install_mode']} | {repo['installer_exit_code']} | {lockfile_icon} |"
        )
    
    md_lines.extend(["", ""])
    
    # Failures section
    failed_repos = [r for r in repos if r["status"] == "failed"]
    
    if failed_repos:
        md_lines.extend([
            "## Failures",
            "",
            "The following repositories failed:",
            "",
        ])
        
        for repo in failed_repos:
            md_lines.extend([
                f"### {Path(repo['path']).name}",
                "",
                f"**Path:** `{repo['path']}`  ",
                f"**Exit Code:** {repo['installer_exit_code']}  ",
                f"**Install Mode:** {repo['install_mode']}  ",
                "",
            ])
            
            if repo.get("notes"):
                md_lines.extend([
                    "**Notes:**",
                    "",
                ])
                for note in repo["notes"]:
                    md_lines.append(f"- {note}")
                md_lines.append("")
            
            # Relative path to log
            log_path = repo["logs"]["install_log_path"]
            if log_path:
                rel_log = Path(log_path).relative_to(out_dir) if Path(log_path).is_absolute() else log_path
                md_lines.extend([
                    "**Log:**",
                    "",
                    f"```bash",
                    f"cat {out_dir}/{rel_log}",
                    f"```",
                    "",
                ])
        
        md_lines.extend([
            "## Remediation",
            "",
            "For failed repositories:",
            "",
            "1. Review the install log for each failed repo",
            "2. Common issues:",
            "   - `taskx doctor` failures → schema bundling issues",
            "   - Git authentication failures → check SSH keys",
            "   - Missing dependencies → install required packages",
            "3. Fix issues and re-run upgrade with `--apply --install`",
            "",
        ])
    
    # Next actions
    md_lines.extend([
        "## Next Actions",
        "",
    ])
    
    if summary["repos_failed"] == 0:
        md_lines.extend([
            "All repositories upgraded successfully! 🎉",
            "",
            "**Verify the upgrade:**",
            "",
            "```bash",
            f"# Re-run verification across all repos",
            f"bash scripts/taskx_upgrade_many.sh --version {rollup_json['target_version']} \\",
            "  --repo-list repos.txt \\",
            "  --apply",
            "```",
            "",
        ])
    else:
        md_lines.extend([
            "**Review failures:**",
            "",
            "1. Check individual repo logs in output directory",
            "2. Fix issues identified in each failing repo",
            "3. Re-run upgrade for failed repos only:",
            "",
            "```bash",
            "# Create a list of failed repo paths",
            "cat > failed_repos.txt <<EOF",
        ])
        
        for repo in failed_repos:
            md_lines.append(repo["path"])
        
        md_lines.extend([
            "EOF",
            "",
            "# Re-run upgrade for failed repos",
            f"bash scripts/taskx_upgrade_many.sh --version {rollup_json['target_version']} \\",
            "  --repo-list failed_repos.txt \\",
            "  --apply --install",
            "```",
            "",
        ])
    
    md_lines.extend([
        "---",
        "",
        f"**Report Location:** `{out_dir}/ROLLUP.md`  ",
        f"**JSON Report:** `{out_dir}/ROLLUP.json`  ",
    ])
    
    return "\n".join(md_lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate TaskX multi-repo upgrade rollup report"
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        required=True,
        help="Output directory containing per-repo result.json files"
    )
    parser.add_argument(
        "--version",
        required=True,
        help="Target TaskX version"
    )
    parser.add_argument(
        "--ref",
        required=True,
        help="Target git ref"
    )
    parser.add_argument(
        "--timestamp-mode",
        choices=["deterministic", "wallclock"],
        default="deterministic",
        help="Timestamp mode"
    )
    
    args = parser.parse_args()
    
    if not args.out_dir.exists():
        print(f"[ERROR] Output directory not found: {args.out_dir}", file=sys.stderr)
        sys.exit(1)
    
    # Load repo results
    results = load_repo_results(args.out_dir)
    
    if not results:
        print("[WARN] No repo results found", file=sys.stderr)
    
    # Generate JSON report
    rollup_json = generate_rollup_json(
        results,
        args.version,
        args.ref,
        args.timestamp_mode
    )
    
    json_path = args.out_dir / "ROLLUP.json"
    with open(json_path, "w") as f:
        json.dump(rollup_json, f, indent=2)
    
    print(f"[INFO] Generated: {json_path}")
    
    # Generate Markdown report
    rollup_md = generate_rollup_md(rollup_json, args.out_dir)
    
    md_path = args.out_dir / "ROLLUP.md"
    with open(md_path, "w") as f:
        f.write(rollup_md)
    
    print(f"[INFO] Generated: {md_path}")
    
    # Exit with status based on failures
    if rollup_json["summary"]["repos_failed"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
