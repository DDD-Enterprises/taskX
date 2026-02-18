"""Base adapter interface for TaskX integration adapters.

All adapters must subclass BaseAdapter and implement the required methods.
Adapters are discovered via the ``taskx.adapters`` entry-point group.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass
from pathlib import Path  # noqa: TC003 — runtime dataclass field
from typing import Any


@dataclass(frozen=True)
class AdapterInfo:
    """Metadata returned by adapter detection.

    Attributes:
        name: Human-readable adapter name (e.g. ``"dopemux"``).
        root: Detected project root for this adapter.
        marker: Which filesystem marker triggered detection.
    """

    name: str
    root: Path
    marker: str


class BaseAdapter(abc.ABC):
    """Abstract base for TaskX integration adapters.

    Subclasses must implement:
    - ``name``          — short identifier (used in CLI ``--adapter`` flag)
    - ``detect``        — detect whether the adapter applies to a directory
    - ``compute_paths`` — return adapter-specific path mappings
    """

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Short, unique adapter identifier (e.g. ``"dopemux"``)."""

    @abc.abstractmethod
    def detect(self, start: Path | None = None) -> AdapterInfo:
        """Detect project root for this adapter.

        Args:
            start: Directory to begin searching from (default: cwd).

        Returns:
            AdapterInfo with root and marker.

        Raises:
            RuntimeError: If detection fails.
        """

    @abc.abstractmethod
    def compute_paths(self, root: Path, **kwargs: Any) -> Any:
        """Compute adapter-specific path mappings.

        Args:
            root: Detected project root.
            **kwargs: Adapter-specific overrides.

        Returns:
            Adapter-specific paths dataclass.
        """
