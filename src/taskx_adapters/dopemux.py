"""Dopemux adapter for TaskX integration.

Provides path detection and mapping to integrate TaskX into Dopemux
projects without modifying TaskX core logic.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from dopetask_adapters.base import AdapterInfo, BaseAdapter
from dopetask_adapters.types import DopemuxDetection, DopemuxPaths


def detect_dopemux_root(start: Path | None = None, override: Path | None = None) -> DopemuxDetection:
    """Detect Dopemux root directory.
    
    Detection priority (first match wins):
    1. Override path if provided
    2. .dopemux/ directory
    3. dopemux.toml file
    4. runtime/ AND lab/ directories both present
    5. .git/ AND dopemux/ directory both present
    
    Args:
        start: Starting directory for search (default: cwd)
        override: Explicit root path to use (skips detection)
        
    Returns:
        DopemuxDetection with root and marker used
        
    Raises:
        RuntimeError: If Dopemux root cannot be detected
    """
    # Use override if provided
    if override is not None:
        if not override.is_dir():
            raise RuntimeError(
                f"Dopemux root override does not exist or is not a directory: {override}"
            )
        return DopemuxDetection(root=override.resolve(), marker_used="override")

    # Start from provided directory or cwd
    current = (start or Path.cwd()).resolve()

    # Walk upward looking for markers
    for _ in range(20):  # Limit search depth
        # Priority 1: .dopemux/ directory
        if (current / ".dopemux").is_dir():
            return DopemuxDetection(root=current, marker_used=".dopemux/")

        # Priority 2: dopemux.toml
        if (current / "dopemux.toml").is_file():
            return DopemuxDetection(root=current, marker_used="dopemux.toml")

        # Priority 3: runtime/ AND lab/ both present
        if (current / "runtime").is_dir() and (current / "lab").is_dir():
            return DopemuxDetection(root=current, marker_used="runtime/ + lab/")

        # Priority 4: .git/ AND dopemux/ both present
        if (current / ".git").is_dir() and (current / "dopemux").is_dir():
            return DopemuxDetection(root=current, marker_used=".git/ + dopemux/")

        # Move up one level
        parent = current.parent
        if parent == current:
            break
        current = parent

    # Not found
    raise RuntimeError(
        "Could not detect Dopemux root.\n"
        "Searched upward from current directory for:\n"
        "  - .dopemux/ directory\n"
        "  - dopemux.toml file\n"
        "  - runtime/ + lab/ directories\n"
        "  - .git/ + dopemux/ directories\n"
        f"Started from: {start or Path.cwd()}\n"
        "Use --dopemux-root to specify explicitly."
    )


def compute_dopemux_paths(
    root: Path,
    out_root_override: Path | None = None,
) -> DopemuxPaths:
    """Compute TaskX paths using Dopemux conventions.
    
    Args:
        root: Dopemux root directory
        out_root_override: Override for out_root (default: root/out/taskx)
        
    Returns:
        DopemuxPaths with all computed paths
    """
    # Determine out_root
    out_root = out_root_override or (root / "out" / "taskx")

    # Compute all output paths
    spec_mine_out = out_root / "spec_mine"
    task_queue_out = out_root / "task_queue"
    runs_out = out_root / "runs"
    spec_feedback_out = out_root / "spec_feedback"
    loop_out = out_root / "loop"

    # Default task queue file
    task_queue_default = task_queue_out / "TASK_QUEUE.json"

    # Detect docs root (best effort)
    docs_root = None
    docs_candidates = [
        root / "docs",
        root / "lab" / "docs",
        root / "runtime" / "docs",
    ]
    for candidate in docs_candidates:
        if candidate.is_dir():
            docs_root = candidate
            break

    return DopemuxPaths(
        out_root=out_root,
        spec_mine_out=spec_mine_out,
        task_queue_out=task_queue_out,
        runs_out=runs_out,
        spec_feedback_out=spec_feedback_out,
        loop_out=loop_out,
        task_queue_default=task_queue_default,
        docs_root=docs_root,
    )


def select_run_folder(runs_out: Path, run: Path | None = None) -> Path:
    """Select a run folder deterministically.
    
    If run is provided, uses it directly.
    Otherwise, selects the lexicographically last folder in runs_out
    (most recent by naming convention like RUN_2026-02-03...).
    
    Args:
        runs_out: Directory containing run folders
        run: Explicit run folder path (optional)
        
    Returns:
        Selected run folder path
        
    Raises:
        RuntimeError: If no run folders exist and run not provided
    """
    # Use explicit run if provided
    if run is not None:
        if not run.is_dir():
            raise RuntimeError(f"Specified run folder does not exist: {run}")
        return run

    # Ensure runs_out exists
    if not runs_out.is_dir():
        raise RuntimeError(
            f"Runs directory does not exist: {runs_out}\n"
            "Cannot auto-select run. Use --run to specify explicitly."
        )

    # Find all run folders (directories only)
    run_folders = sorted(
        [d for d in runs_out.iterdir() if d.is_dir()],
        reverse=True,  # Descending order (most recent first)
    )

    if not run_folders:
        raise RuntimeError(
            f"No run folders found in: {runs_out}\n"
            "Cannot auto-select run. Use --run to specify explicitly."
        )

    # Return first (most recent)
    return run_folders[0]


class DopemuxAdapter(BaseAdapter):
    """BaseAdapter implementation for Dopemux projects."""

    @property
    def name(self) -> str:
        return "dopemux"

    def detect(self, start: Path | None = None) -> AdapterInfo:
        """Detect Dopemux root, delegating to ``detect_dopemux_root``."""
        detection = detect_dopemux_root(start=start)
        return AdapterInfo(
            name=self.name,
            root=detection.root,
            marker=detection.marker_used,
        )

    def compute_paths(self, root: Path, **kwargs: Any) -> DopemuxPaths:
        """Compute Dopemux paths, delegating to ``compute_dopemux_paths``."""
        return compute_dopemux_paths(root, out_root_override=kwargs.get("out_root_override"))
