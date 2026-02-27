#!/usr/bin/env python3
"""
A16_MIN.12 — Repo Discovery Report Generator

Reads discovery_raw.json and generates:
  - DISCOVERY_REPORT.json (structured report)
  - DISCOVERY_REPORT.md (human-readable report)

Usage:
    python scripts/dopetask_discover_repos_report.py \\
        --in out/dopetask_repo_discovery/discovery_raw.json \\
        --out out/dopetask_repo_discovery \\
        --timestamp-mode deterministic
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timezone


def get_timestamp(mode="deterministic"):
    """Get timestamp based on mode."""
    if mode == "deterministic":
        return "1970-01-01T00:00:00Z"
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_discovery_data(input_file):
    """Load discovery_raw.json."""
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file not found: {input_file}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {input_file}: {e}", file=sys.stderr)
        sys.exit(1)


def generate_discovery_report_json(discovery_data):
    """Generate DISCOVERY_REPORT.json from discovery_raw.json.
    
    This is essentially a passthrough with validation since the raw format
    matches the final report format.
    """
    return {
        "schema_version": discovery_data.get("schema_version", "1.0"),
        "generated_at": discovery_data.get("generated_at"),
        "timestamp_mode": discovery_data.get("timestamp_mode", "deterministic"),
        "root": discovery_data.get("root"),
        "depth": discovery_data.get("depth"),
        "max_repos": discovery_data.get("max_repos"),
        "include_non_git": discovery_data.get("include_non_git"),
        "symlinks": discovery_data.get("symlinks"),
        "summary": discovery_data.get("summary", {}),
        "repos": sorted(discovery_data.get("repos", []), key=lambda x: x["path"])
    }


def generate_discovery_report_md(discovery_data):
    """Generate DISCOVERY_REPORT.md (human-readable)."""
    lines = []
    
    # Title
    lines.append("# dopeTask Repository Discovery Report")
    lines.append("")
    
    # Metadata
    lines.append(f"**Scan Root:** `{discovery_data['root']}`")
    lines.append(f"**Max Depth:** {discovery_data['depth']}")
    lines.append(f"**Max Repos:** {discovery_data['max_repos']}")
    lines.append(f"**Include Non-Git:** {discovery_data['include_non_git']}")
    lines.append(f"**Follow Symlinks:** {discovery_data['symlinks']}")
    lines.append(f"**Generated:** {discovery_data['generated_at']}")
    lines.append("")
    
    # Summary
    summary = discovery_data["summary"]
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Total Repos Found:** {summary['repos_found']}")
    lines.append(f"- **Repos Emitted:** {summary['repos_emitted']}")
    lines.append(f"- **Truncated:** {'Yes ⚠️' if summary['truncated'] else 'No'}")
    lines.append("")
    
    # Warnings
    if summary.get("truncated"):
        lines.append("## ⚠️ Warnings")
        lines.append("")
        lines.append(f"**Truncation:** Discovery found {summary['repos_found']} repos, "
                    f"but output was limited to {summary['repos_emitted']} repos. "
                    f"Increase `--max-repos` to capture all repos.")
        lines.append("")
    
    if discovery_data.get("symlinks"):
        if not summary.get("truncated"):
            lines.append("## ⚠️ Warnings")
            lines.append("")
        lines.append("**Symlink Mode:** Symlinks were followed during discovery. "
                    "This may lead to duplicate or unexpected results.")
        lines.append("")
    
    # Repositories
    repos = discovery_data.get("repos", [])
    
    if len(repos) == 0:
        lines.append("## Discovered Repositories")
        lines.append("")
        lines.append("*No repositories found.*")
        lines.append("")
    elif len(repos) <= 50:
        # Show all repos if <= 50
        lines.append("## Discovered Repositories")
        lines.append("")
        lines.append("| Repository | Git Repo |")
        lines.append("|------------|----------|")
        for repo in sorted(repos, key=lambda x: x["path"]):
            git_icon = "✅" if repo.get("git_repo") else "❌"
            lines.append(f"| `{repo['path']}` | {git_icon} |")
        lines.append("")
    else:
        # Show first 20 and last 20 if > 50
        lines.append("## Discovered Repositories")
        lines.append("")
        lines.append(f"*Showing first 20 and last 20 of {len(repos)} repos. "
                    f"See `REPOS.txt` for complete list.*")
        lines.append("")
        lines.append("### First 20 Repositories")
        lines.append("")
        lines.append("| Repository | Git Repo |")
        lines.append("|------------|----------|")
        sorted_repos = sorted(repos, key=lambda x: x["path"])
        for repo in sorted_repos[:20]:
            git_icon = "✅" if repo.get("git_repo") else "❌"
            lines.append(f"| `{repo['path']}` | {git_icon} |")
        lines.append("")
        
        lines.append("### Last 20 Repositories")
        lines.append("")
        lines.append("| Repository | Git Repo |")
        lines.append("|------------|----------|")
        for repo in sorted_repos[-20:]:
            git_icon = "✅" if repo.get("git_repo") else "❌"
            lines.append(f"| `{repo['path']}` | {git_icon} |")
        lines.append("")
    
    # Statistics
    git_count = sum(1 for r in repos if r.get("git_repo"))
    non_git_count = len(repos) - git_count
    
    lines.append("## Repository Statistics")
    lines.append("")
    lines.append(f"- **Git Repos:** {git_count}")
    lines.append(f"- **Non-Git Repos:** {non_git_count}")
    lines.append("")
    
    # Next Steps
    lines.append("## Next Steps")
    lines.append("")
    lines.append("### 1. Review Discovered Repositories")
    lines.append("")
    lines.append("```bash")
    lines.append("cat out/dopetask_repo_discovery/REPOS.txt")
    lines.append("```")
    lines.append("")
    
    lines.append("### 2. Audit Version Drift")
    lines.append("")
    lines.append("```bash")
    lines.append("bash scripts/dopetask_pin_audit.sh \\")
    lines.append("  --target-version X.Y.Z \\")
    lines.append("  --repo-list out/dopetask_repo_discovery/REPOS.txt")
    lines.append("")
    lines.append("cat out/dopetask_pin_audit/PIN_AUDIT.md")
    lines.append("```")
    lines.append("")
    
    lines.append("### 3. Upgrade Behind Repositories")
    lines.append("")
    lines.append("```bash")
    lines.append("bash scripts/dopetask_upgrade_many.sh \\")
    lines.append("  --version X.Y.Z \\")
    lines.append("  --repo-list out/dopetask_repo_discovery/REPOS.txt \\")
    lines.append("  --apply")
    lines.append("")
    lines.append("cat out/dopetask_upgrade_many/ROLLUP.md")
    lines.append("```")
    lines.append("")
    
    return "\n".join(lines)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate dopeTask repo discovery reports from discovery_raw.json"
    )
    parser.add_argument(
        "--in",
        dest="input_file",
        required=True,
        help="Path to discovery_raw.json"
    )
    parser.add_argument(
        "--out",
        dest="output_dir",
        required=True,
        help="Output directory for reports"
    )
    parser.add_argument(
        "--timestamp-mode",
        choices=["deterministic", "wallclock"],
        default="deterministic",
        help="Timestamp mode (default: deterministic)"
    )
    
    args = parser.parse_args()
    
    # Load discovery data
    discovery_data = load_discovery_data(args.input_file)
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate JSON report
    report_json = generate_discovery_report_json(discovery_data)
    json_path = output_dir / "DISCOVERY_REPORT.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report_json, f, indent=2, ensure_ascii=False)
        f.write("\n")
    
    print(f"Generated: {json_path}")
    
    # Generate MD report
    report_md = generate_discovery_report_md(discovery_data)
    md_path = output_dir / "DISCOVERY_REPORT.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(report_md)
    
    print(f"Generated: {md_path}")
    
    # Print summary
    summary = discovery_data["summary"]
    print("")
    print("=" * 70)
    print("DISCOVERY SUMMARY")
    print("=" * 70)
    print(f"Repos Found:   {summary['repos_found']}")
    print(f"Repos Emitted: {summary['repos_emitted']}")
    print(f"Truncated:     {summary['truncated']}")
    print("=" * 70)


if __name__ == "__main__":
    main()
