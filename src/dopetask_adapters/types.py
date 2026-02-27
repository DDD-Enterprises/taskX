"""Type definitions for dopeTask adapters."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DopemuxDetection:
    """Result of Dopemux root detection.

    Attributes:
        root: Detected Dopemux root directory
        marker_used: Which marker was used for detection
    """

    root: Path
    marker_used: str


@dataclass(frozen=True)
class DopemuxPaths:
    """Computed paths for Dopemux integration.

    All paths follow Dopemux conventions:
    - out_root: Base output directory (dopemux_root/out/dopetask)
    - spec_mine_out: Spec mining outputs
    - task_queue_out: Task queue files
    - runs_out: Task run outputs
    - spec_feedback_out: Spec feedback outputs
    - loop_out: Loop orchestration outputs
    - task_queue_default: Default task queue file path
    - docs_root: Documentation root (if detected)
    """

    out_root: Path
    spec_mine_out: Path
    task_queue_out: Path
    runs_out: Path
    spec_feedback_out: Path
    loop_out: Path
    task_queue_default: Path
    docs_root: Path | None
