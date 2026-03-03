"""Compatibility helpers for TOML parsing across supported Python versions."""

from __future__ import annotations

import importlib
from types import ModuleType


def load_tomllib() -> ModuleType:
    """Load the stdlib TOML parser or fall back to the backport on Python 3.9/3.10."""
    try:
        return importlib.import_module("tomllib")
    except ModuleNotFoundError:
        return importlib.import_module("tomli")


tomllib = load_tomllib()
