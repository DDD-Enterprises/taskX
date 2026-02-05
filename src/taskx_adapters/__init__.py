"""TaskX adapters for integrating with external systems.

Adapters provide thin shims that map external project structures
to TaskX expectations without modifying TaskX core logic.
"""

from taskx_adapters.dopemux import (
    compute_dopemux_paths,
    detect_dopemux_root,
    select_run_folder,
)
from taskx_adapters.types import DopemuxDetection, DopemuxPaths

__all__ = [
    "DopemuxDetection",
    "DopemuxPaths",
    "compute_dopemux_paths",
    "detect_dopemux_root",
    "select_run_folder",
]
