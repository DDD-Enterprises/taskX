import hashlib
import json
import os
import shutil
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from rich.console import Console

console = Console()

class BundleExporter:
    """Handles deterministic export of case bundles."""

    def __init__(self, repo_root: Path, config_path: Path | None = None):
        self.repo_root = repo_root.resolve()
        self.config = self._load_config(config_path)

    def _load_config(self, config_path: Path | None) -> dict[str, Any]:
        """Load config from file or use defaults."""
        defaults = {
            "logs": {
                "globs": ["**/*.log", "**/*.out", "**/*.err"],
                "caps": {"per_file_max_mb": 25, "total_logs_max_mb": 250, "max_files": 10000},
                "excludes": ["**/node_modules/**", "**/.git/**", "**/.venv/**", "**/__pycache__/**"]
            }
        }

        path = config_path or (self.repo_root / "dopetask_bundle.yaml")
        if path.exists():
            try:
                with open(path) as f:
                    user_config = yaml.safe_load(f)
                    # Deep merge would be better, but simple overlay is fine for now
                    if user_config:
                        defaults.update(user_config)
            except Exception as e:
                console.print(f"[yellow]Warning: Failed to load config {path}: {e}[/yellow]")

        return defaults

    def collect_dopetask_artifacts(self, last_n: int, temp_dir: Path) -> list[str]:
        """Collect last N runs and task packets."""
        dopetask_dir = temp_dir / "dopetask"
        dopetask_dir.mkdir(parents=True, exist_ok=True)

        manifest_entries = []

        # 1. Task Queue
        queue_path = self.repo_root / "out" / "tasks" / "task_queue.json"
        if queue_path.exists():
            dest = dopetask_dir / "task_queue.json"
            shutil.copy2(queue_path, dest)
            manifest_entries.append("dopetask/task_queue.json")

        # 2. Packets (simplified: verify existence, but complex logic omitted for brevity)
        # 3. Runs (simplified: copy last N folders)
        runs_dir = self.repo_root / "out" / "runs"
        if runs_dir.exists():
            all_runs = sorted(runs_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
            for run in all_runs[:last_n]:
                if not run.is_dir():
                    continue
                dest_run = dopetask_dir / "runs" / run.name
                shutil.copytree(run, dest_run)
                # Walk and add to manifest
                for root, _, files in os.walk(dest_run):
                    for file in files:
                        rel_path = Path(root).relative_to(temp_dir) / file
                        manifest_entries.append(str(rel_path))

        return manifest_entries

    def collect_repo_snapshot(self, temp_dir: Path) -> str:
        """Generate REPO_SNAPSHOT.json."""
        repo_dir = temp_dir / "repo"
        repo_dir.mkdir(parents=True, exist_ok=True)

        snapshot = {
            "timestamp": datetime.now(UTC).isoformat(),
            "git_available": False,
            "head_sha": None,
            "branch": None
        }

        # Try git
        if (self.repo_root / ".git").exists():
            try:
                import subprocess
                head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.repo_root).decode().strip()
                branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=self.repo_root).decode().strip()
                snapshot["git_available"] = True
                snapshot["head_sha"] = head
                snapshot["branch"] = branch
            except Exception:
                pass

        snapshot_path = repo_dir / "REPO_SNAPSHOT.json"
        with open(snapshot_path, "w") as f:
            json.dump(snapshot, f, indent=2)

        return "repo/REPO_SNAPSHOT.json"

    def collect_repo_logs(self, temp_dir: Path) -> list[str]:
        """Collect logs based on config capabilities."""
        logs_out_dir = temp_dir / "repo" / "logs"
        logs_out_dir.mkdir(parents=True, exist_ok=True)

        log_index: dict[str, list[dict[str, Any]]] = {
            "included": [],
            "skipped": []
        }

        manifest_entries = []

        # Simple glob implementation
        globs = self.config["logs"].get("globs", [])
        excludes = self.config["logs"].get("excludes", [])

        # Gather candidates
        candidates = set()
        for g in globs:
            for path in self.repo_root.glob(g):
                if path.is_file():
                    candidates.add(path)

        # Filter excludes
        final_list = []
        for path in candidates:
            rel = path.relative_to(self.repo_root)
            # Check excludes (naive)
            is_excluded = False
            for ex in excludes:
                # Basic match check
                if ex.strip("/") in str(rel): # Simplification
                    is_excluded = True
                    break
            if not is_excluded:
                final_list.append(path)

        # Copy with caps logic
        total_size = 0
        max_total = self.config["logs"]["caps"]["total_logs_max_mb"] * 1024 * 1024

        for path in final_list:
            size = path.stat().st_size
            rel_path = path.relative_to(self.repo_root)

            if size > self.config["logs"]["caps"]["per_file_max_mb"] * 1024 * 1024:
                log_index["skipped"].append({"path": str(rel_path), "reason": "size_limit"})
                continue

            if total_size + size > max_total:
                 log_index["skipped"].append({"path": str(rel_path), "reason": "total_cap_hit"})
                 continue

            # Copy
            dest = logs_out_dir / rel_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)

            total_size += size
            log_index["included"].append({"path": str(rel_path), "size": size})
            manifest_entries.append(f"repo/logs/{rel_path}")

        # Write index
        index_path = temp_dir / "repo" / "LOG_INDEX.json"
        with open(index_path, "w") as f:
            json.dump(log_index, f, indent=2)
        manifest_entries.append("repo/LOG_INDEX.json")

        return manifest_entries

    def _sha256_file(self, path: Path) -> str:
        """Compute SHA256 for a file."""
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _classify_path(self, rel_path: str) -> str:
        """Classify a bundled file deterministically by path."""
        normalized = rel_path.replace("\\", "/")
        if normalized == "dopetask/task_queue.json":
            return "dopetask_task_queue"
        if normalized.startswith("dopetask/packets/") or (
            normalized.startswith("dopetask/runs/") and normalized.endswith("/TASK_PACKET.md")
        ):
            return "dopetask_packet"
        if normalized.startswith("dopetask/runs/"):
            return "dopetask_run_artifact"
        if normalized == "repo/REPO_SNAPSHOT.json":
            return "repo_snapshot"
        if normalized.startswith("repo/logs/") or normalized == "repo/LOG_INDEX.json":
            return "repo_log"
        if normalized.startswith("reports/"):
            return "report"
        return "unknown"

    def _collect_file_entries(self, temp_dir: Path) -> list[dict[str, Any]]:
        """Collect deterministic file metadata for CASE_MANIFEST.files."""
        entries: list[dict[str, Any]] = []
        for path in sorted(p for p in temp_dir.rglob("*") if p.is_file()):
            rel = path.relative_to(temp_dir).as_posix()
            if rel == "case/CASE_MANIFEST.json":
                continue
            entries.append(
                {
                    "path": rel,
                    "sha256": self._sha256_file(path),
                    "size_bytes": path.stat().st_size,
                    "category": self._classify_path(rel),
                }
            )
        return entries

    def build_case_manifest(self, temp_dir: Path, case_id: str) -> None:
        """Generate manifest for the entire bundle."""
        case_dir = temp_dir / "case"
        case_dir.mkdir(parents=True, exist_ok=True)
        files = self._collect_file_entries(temp_dir)
        manifest_hash_input = "\n".join(
            f"{entry['path']}|{entry['sha256']}|{entry['size_bytes']}" for entry in files
        )
        manifest_hash = hashlib.sha256(manifest_hash_input.encode("utf-8")).hexdigest()

        manifest = {
            "schema_version": "1.0",
            "case_id": case_id,
            "generated_at": datetime.now(UTC).isoformat(),
            "bundle_manifest": {
                "sha256": manifest_hash,
                "source_label": "dopetask-export",
                "created_at": datetime.now(UTC).isoformat(),
            },
            "contents": {
                "task_queue": "dopetask/task_queue.json",
                "repo_snapshot": "repo/REPO_SNAPSHOT.json",
                "logs_index": "repo/LOG_INDEX.json",
            },
            "files": files,
        }

        with open(case_dir / "CASE_MANIFEST.json", "w") as f:
            json.dump(manifest, f, indent=2)

    def export(self, last_n: int, out_dir: Path, case_id: str | None = None) -> Path:
        """Main export flow."""
        import tempfile

        if not case_id:
            ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            case_id = f"CASE_{ts}"

        console.print(f"[cyan]Exporting Case Bundle: {case_id}[/cyan]")

        with tempfile.TemporaryDirectory() as td:
            temp_path = Path(td)

            # 1. Artifacts
            self.collect_dopetask_artifacts(last_n, temp_path)

            # 2. Snapshot
            self.collect_repo_snapshot(temp_path)

            # 3. Logs
            self.collect_repo_logs(temp_path)

            # 4. Manifest
            self.build_case_manifest(temp_path, case_id)

            # 5. Zip
            out_dir.mkdir(parents=True, exist_ok=True)
            zip_path = out_dir / f"{case_id}.zip"

            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for root, _, files in os.walk(temp_path):
                    for file in files:
                        abs_path = Path(root) / file
                        rel_path = abs_path.relative_to(temp_path)
                        zf.write(abs_path, rel_path)

            console.print(f"[green]Bundle exported to: {zip_path}[/green]")
            return zip_path
