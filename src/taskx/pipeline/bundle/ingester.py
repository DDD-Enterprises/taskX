
import json
import logging
import shutil
import zipfile
from pathlib import Path
from typing import Any, Dict, Optional, List
from datetime import datetime, UTC

from rich.console import Console
from taskx.utils.schema_registry import get_schema_json
from jsonschema import validate

console = Console()

class BundleIngester:
    """Handles secure ingestion and validation of case bundles."""

    def __init__(self, out_dir: Path):
        self.out_dir = out_dir.resolve()

    def extract_bundle(self, zip_path: Path) -> Path:
        """Securely extract bundle to out_dir."""
        if not zip_path.exists():
            raise FileNotFoundError(f"Bundle zip not found: {zip_path}")

        # Create a unique extract dir based on zip name or timestamp
        extract_root = self.out_dir / zip_path.stem
        if extract_root.exists():
            shutil.rmtree(extract_root)
        extract_root.mkdir(parents=True, exist_ok=True)

        console.print(f"[cyan]Extracting {zip_path.name} to {extract_root}...[/cyan]")
        
        with zipfile.ZipFile(zip_path, 'r') as zf:
            # Basic security: prevent path traversal
            for member in zf.infolist():
                filename = member.filename
                if filename.startswith('/') or '..' in filename:
                    raise ValueError(f"Malicious filename detected in zip: {filename}")
            zf.extractall(extract_root)
            
        return extract_root

    def validate_manifest(self, case_dir: Path) -> Dict[str, Any]:
        """Validate CASE_MANIFEST.json against schema and integrity rules."""
        manifest_path = case_dir / "case" / "CASE_MANIFEST.json"
        if not manifest_path.exists():
            raise FileNotFoundError(f"CASE_MANIFEST.json missing in {case_dir}")

        with open(manifest_path) as f:
            manifest_data = json.load(f)

        # Validate against schema
        schema = get_schema_json("case_bundle")
        validate(instance=manifest_data, schema=schema)
        
        # Integrity checks (placeholder for actual SHA256 validation of contents)
        # In a full implementation, we would verify hashes of all files listed in manifest
        
        return manifest_data

    def generate_case_index(self, case_dir: Path) -> Path:
        """Scan the extracted bundle and generate a searchable CASE_INDEX.json."""
        index_path = case_dir / "CASE_INDEX.json"
        
        index = {
            "case_id": case_dir.name,
            "ingested_at": datetime.now(UTC).isoformat(),
            "structure": {
                "taskx": {
                    "packets": [str(p.relative_to(case_dir)) for p in (case_dir / "taskx").glob("packets/*.md")],
                    "runs": [str(r.relative_to(case_dir)) for r in (case_dir / "taskx").glob("runs/*") if r.is_dir()],
                    "queue": str((case_dir / "taskx" / "task_queue.json").relative_to(case_dir)) if (case_dir / "taskx" / "task_queue.json").exists() else None
                },
                "repo": {
                    "snapshot": str((case_dir / "repo" / "REPO_SNAPSHOT.json").relative_to(case_dir)) if (case_dir / "repo" / "REPO_SNAPSHOT.json").exists() else None,
                    "logs": [str(l.relative_to(case_dir)) for l in (case_dir / "repo" / "logs").rglob("*") if l.is_file()]
                }
            }
        }

        with open(index_path, "w") as f:
            json.dump(index, f, indent=2)
            
        return index_path

    def ingest(self, zip_path: Path) -> Path:
        """Main ingest flow."""
        # 1. Extract
        case_dir = self.extract_bundle(zip_path)
        
        # 2. Validate
        try:
            self.validate_manifest(case_dir)
            console.print("[green]✓ Manifest validated successfully.[/green]")
        except Exception as e:
            console.print(f"[bold red]Validation Failed:[/bold red] {e}")
            # Optional: clean up on fail?
            raise

        # 3. Index
        index_path = self.generate_case_index(case_dir)
        console.print(f"[green]✓ Case index generated: {index_path.relative_to(case_dir)}[/green]")
        
        return case_dir
