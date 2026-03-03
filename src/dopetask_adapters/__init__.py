"""dopeTask adapters for integrating with external systems.

Adapters provide thin shims that map external project structures
to dopeTask expectations without modifying dopeTask core logic.

Discovery uses the ``dopetask.adapters`` entry-point group so that
third-party packages can register adapters automatically.
"""

from __future__ import annotations

import importlib.metadata as importlib_metadata
import typing
from typing import TYPE_CHECKING

from dopetask_adapters.base import AdapterInfo, BaseAdapter
from dopetask_adapters.dopemux import (
    DopemuxAdapter,
    compute_dopemux_paths,
    detect_dopemux_root,
    select_run_folder,
)
from dopetask_adapters.types import DopemuxDetection, DopemuxPaths

if TYPE_CHECKING:
    from collections.abc import Iterator

__all__ = [
    "AdapterInfo",
    "BaseAdapter",
    "DopemuxAdapter",
    "DopemuxDetection",
    "DopemuxPaths",
    "compute_dopemux_paths",
    "detect_dopemux_root",
    "discover_adapters",
    "get_adapter",
    "select_run_folder",
]


def _adapter_entry_points() -> typing.Iterable[typing.Any]:
    """Return adapter entry points across Python 3.9+ metadata APIs."""
    eps = typing.cast(typing.Any, importlib_metadata.entry_points())
    if hasattr(eps, "select"):
        return typing.cast(typing.Iterable[typing.Any], eps.select(group="dopetask.adapters"))
    if isinstance(eps, dict):
        return typing.cast(typing.Iterable[typing.Any], eps.get("dopetask.adapters", ()))
    return typing.cast(
        typing.Iterable[typing.Any],
        [ep for ep in eps if getattr(ep, "group", None) == "dopetask.adapters"],
    )


def discover_adapters() -> Iterator[BaseAdapter]:
    """Yield all adapters registered under the ``dopetask.adapters`` entry-point group.

    Supports both selectable and legacy ``importlib.metadata.entry_points()`` return values.
    """
    for ep in _adapter_entry_points():
        adapter_cls = ep.load()
        if isinstance(adapter_cls, type) and issubclass(adapter_cls, BaseAdapter):
            yield adapter_cls()
        elif callable(adapter_cls):
            instance = adapter_cls()
            if isinstance(instance, BaseAdapter):
                yield instance


def get_adapter(name: str) -> typing.Optional[BaseAdapter]:
    """Return the first adapter whose ``name`` matches, or ``None``."""
    for adapter in discover_adapters():
        if adapter.name == name:
            return adapter
    return None
